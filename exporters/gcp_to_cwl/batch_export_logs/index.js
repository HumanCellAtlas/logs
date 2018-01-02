const runtimeConfig = require('cloud-functions-runtime-config');
const AWS = require('aws-sdk');
const Maybe = require('maybe');
const PubSub = require(`@google-cloud/pubsub`);
const pubsub = require('./pubsub');


/**
 * batchExportLogs Cloud Function.
 *
 * @param {object} event a timer event initiating the export
 * @param {function} callback a callback function
 */
exports.batchExportLogs = function (event, callback) {
  if (!event.data) callback(); // no data

  const projectId = process.env.GCLOUD_PROJECT;

  const topicUri = Buffer.from(event.data.data, 'base64').toString();
  const topicName = topicUri.split('/').pop();
  const subscriptionName = topicName;

  const [logPrefix, resourceType, resourceName] = topicName.split('.');
  const logGroup = getLogGroup(resourceType, resourceName);
  const logStream = 'default';

  const logExportBatchSize = 1000;

  Promise.all(
    [
      runtimeConfig.getVariable('log-exporter', 'AWS_ACCESS_KEY_ID'),
      runtimeConfig.getVariable('log-exporter', 'AWS_SECRET_ACCESS_KEY'),
      runtimeConfig.getVariable('log-exporter', 'AWS_REGION'),
      createSubscriptionIfDoesNotExist(subscriptionName),
    ]
  ).then(credentials => {
    const [awsAccessKeyId, awsSecretAccessKey, awsRegion, subscription] = credentials

    var cloudwatchlogs = new AWS.CloudWatchLogs({
      accessKeyId: awsAccessKeyId,
      secretAccessKey: awsSecretAccessKey,
      region: awsRegion
    });

    var batchClient = new pubsub.SynchronousPullClient(projectId, subscriptionName);

    // pull 1000 log entries at a time, export them, and ack them
    // repeat until there are at most 500 log entries remaining in the queue
    function recurse(maybeUploadSequenceToken) {
      return batchClient.pull(logExportBatchSize, (envelope) => {
        var [logEntries, ackIds] = exports.openSynchronousPullEnvelope(envelope);
        if (logEntries.length == 0) return 'done';
        const moreLogs = logEntries.length == logExportBatchSize;
        return exportLogEntries(cloudwatchlogs, logGroup, logStream, logEntries, maybeUploadSequenceToken)
          .then(uploadSequenceToken => batchClient.ack(
            ackIds,
            x => moreLogs ? recurse(uploadSequenceToken) : 'done'
          ));
      });
    }
    recurse(new Maybe())
      .then(any => callback())
      .catch(err => {
        console.log("Failed on input: " + JSON.stringify(event));
        throw err;
      });
  });
}


getLogGroup = function(resourceType, resourceName) {
  return `/gcp/${resourceType}/${resourceName}`;
}


decode = function(data) {
  return JSON.parse(Buffer.from(data, 'base64').toString());
}


exports.openSynchronousPullEnvelope = function(envelope) {
  var ackIds = envelope.receivedMessages.map(m => m.ackId);
  var logEntries = envelope.receivedMessages.map(m => decode(m.message.data));
  return [logEntries, ackIds];
}


exports.streamUntil = function(request, processResponse, processError) {
  function recurse(currentRequest) {
    return currentRequest.then(
      function(response) {
        var [nextRequest, result] = processResponse(response);
        if (nextRequest != null) {
          return recurse(nextRequest);
        } else {
          return result;
        }
      },
      function (err) {
        var result = processError(err)
        if (result != null) {
          return result
        } else {
          throw err
        }
      }
    );
  }
  return recurse(request);
}


function createSubscriptionIfDoesNotExist(topicName) {
  const pubsub = PubSub()
  const topic = pubsub.topic(topicName)
  return topic.getSubscriptions()
    .then(function(data) {
        const subscriptions = data[0]
        const subscriptionNames = subscriptions.map(s => s.name.split('/').pop());
        const ind = subscriptionNames.indexOf(topicName);
        if (ind > -1) {
          return subscriptions[ind]
        } else {
          return topic.createSubscription(topicName).then(result => result[0])
        }
    })
}


// TODO: untangle this
function exportLogEntries(cloudwatchlogs, logGroup, logStream, logEntries, maybeUploadSequenceToken) {

  const twentyThreeHours = 23*60*60*1000;
  const twentyThreeHoursAgo = new Date().getTime() - twentyThreeHours;

  var request = {
    logGroupName: logGroup,
    logStreamName: logStream,
    logEvents: logEntries
      .filter(function(a) {
        // TODO: CloudWatchLogs does not accept groups of log events with spans wider than 24 hours
        // either group these or set guidelines in place that old log entries will be dropped.
        // ALSO: CloudWatchLogs does not accept log entries which have no message
        return a.timestamp > twentyThreeHoursAgo && a.message != undefined;
      })
      .sort(function(a, b) {
        return a.timestamp - b.timestamp;
      })
  }

  // if there are no log events to ship, stop!
  if (request.logEvents.length == 0) return Promise.resolve(new Maybe());

  var status = {
    logGroup: logGroup,
    logStream: logStream,
    logGroupExists: undefined,
    logStreamExists: undefined,
    uploadToken: undefined,
  }

  if (maybeUploadSequenceToken.isJust()) {
    status.logGroupExists = true;
    status.logStreamExists = true;
    status.uploadToken = maybeUploadSequenceToken.value();
  }

  function updateStatus(cloudwatchlogs, status) {
    return exports.streamUntil(
      cloudwatchlogs.describeLogStreams({
        logGroupName: status.logGroup,
        logStreamNamePrefix: status.logStream,
      }).promise(),
      function(response) {
        for (var stream of response.logStreams) {
          if (stream.logStreamName == status.logStream) {
            status.logGroupExists = true;
            status.logStreamExists = true;
            status.uploadToken = stream.uploadSequenceToken;
            return [null, status];
          }
        }
        var hasNext = response.nextToken != null
        var nextPage = hasNext ? cloudwatchlogs.describeLogStreams({nextToken: response.nextToken}) : null
        return [nextPage, status];
      },
      function(err) {
        if (err.code == 'ResourceNotFoundException') {
          status.logGroupExists = false;
          status.logStreamExists = false;
          return status;
        } else {
          throw err
        }
      }
    )
  }

  function getUploadTokenIfPossible(status) {
    if (status.uploadToken != undefined) return Promise.resolve(status)
    return updateStatus(cloudwatchlogs, status)
  }

  function createLogGroupIfNeeded(status) {
    if (status.logGroupExists) {
      console.log(`Log group/stream exists, obtained sequence token: ${status.uploadToken}`);
      return Promise.resolve(status);
    }
    console.log(`Log group ${logGroup} does not exist, creating it.`);
    return cloudwatchlogs.createLogGroup({logGroupName: logGroup})
      .promise()
      .then(any => {
        status.logGroupExists = true;
        return status;
      });
  }

  function createLogStreamIfNeeded(status) {
    if (status.logStreamExists) return Promise.resolve(status);
    console.log(`Log stream ${logStream} does not exist or is unknown, attempting to create it.`);
    return cloudwatchlogs.createLogStream({logGroupName: logGroup, logStreamName: logStream})
      .promise()
      .then(any => {
        status.logStreamExists = true;
        status.uploadToken = null;
        return status;
      })
      .catch(err => {
        if (err.code != 'ResourceAlreadyExistsException') throw err
        console.log(`Log stream ${logStream} already existed, retreiving sequence token.`);
        return status.update(cloudwatchlogs)
      })
  }

  function putLogEvents(status) {
    request.sequenceToken = status.uploadToken;
    return cloudwatchlogs.putLogEvents(request)
      .promise()
      .then(result => {
        console.log(`Uploaded ${logEntries.length} events, next sequence token: ${result.nextSequenceToken}`)
        return new Maybe(result.nextSequenceToken)
      });
  }

  return getUploadTokenIfPossible(status)
    .then(status => createLogGroupIfNeeded(status))
    .then(status => createLogStreamIfNeeded(status))
    .then(status => putLogEvents(status))
}