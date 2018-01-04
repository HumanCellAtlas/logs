const AWS = require('aws-sdk');
const PubSub = require(`@google-cloud/pubsub`);
const pubsub = require('./pubsub');
var zlib = require('zlib');
var fs = require('fs');

const BATCH_SIZE = 2500;
const AWS_REGION = process.env.REGION;
const PROJECT_ID = process.env.GCLOUD_PROJECT;
const LOG_TOPIC_SUBSCRIPTION_NAME = process.env.LOG_TOPIC_SUBSCRIPTION_NAME;

exports.handler = function(input, context) {
  exports.withCredentials(context, function() {
    var batchClient = new pubsub.SynchronousPullClient({
      projectId: PROJECT_ID,
      subscription: LOG_TOPIC_SUBSCRIPTION_NAME,
    });
    var cloudwatchlogs = new AWS.CloudWatchLogs({region: AWS_REGION});
    var sequenceTokenCache = {};

    return batchClient.stream(
      BATCH_SIZE,
      function(unformattedLogEntries) {
        var requests = exports.groupEntriesIntoRequests(unformattedLogEntries);
        return Promise.all(
          requests.map(request => exports.putLogEvents(cloudwatchlogs, request, sequenceTokenCache))
        )
        .catch(err => {
          console.log("Failed on input: " + JSON.stringify(input));
          console.log(err);
          return cleanup(context, unlinkErr => context.fail(err));
        });
      },
      function() {
        return cleanup(context, err => err ? context.fail(err) : context.succeed('Done'));
      }
    )
  });
}


////
// credentials
//
exports.withCredentials = function(context, callback) {
  var credentialsString = process.env.GCLOUD_CREDENTIALS;
  var credentialsFile = process.env.GOOGLE_APPLICATION_CREDENTIALS;
  return zlib.gunzip(
    new Buffer(credentialsString, 'base64'),
    function(err, buffer) {
      fs.writeFile(
        credentialsFile,
        buffer.toString('utf8'),
        function(err) {
          if (err) {
            return context.fail(err);
          } else {
            return callback();
          }
        }
      )
    }
  )
}

var cleanup = function(context, callback) {
  var credentialsFile = process.env.GOOGLE_APPLICATION_CREDENTIALS;
  return fs.unlink(credentialsFile, err => {
    var errParam = err && err.code =='ENOENT' ? null : err;
    callback(errParam);
  });
}


////
// log export
//
exports.groupEntriesIntoRequests = function(unformattedLogEntries) {
  const twentyThreeHours = 23*60*60*1000;
  const twentyThreeHoursAgo = new Date().getTime() - twentyThreeHours;

  var requests = {};

  for (var unformattedLogEntry of unformattedLogEntries) {
    var logGroup = getLogGroup(unformattedLogEntry);
    var logEntry = exports.formatLogEntry(unformattedLogEntry);

    if (!(logGroup in requests)) {
      requests[logGroup] = {
        logGroupName: logGroup,
        logStreamName: 'default',
        logEvents: []
      };
    }

    if (logEntry.timestamp >= twentyThreeHoursAgo) {
      requests[logGroup].logEvents.push(logEntry);
    }
  }
  return Object.keys(requests).map(key => {
    requests[key].logEvents.sort(function(a, b) {
      return a.timestamp - b.timestamp;
    });
    return requests[key]
  });
}


exports.putLogEvents = function(cloudwatchlogs, request, sequenceTokenCache) {
  var cacheKey = `${request.logGroupName}:${request.logStreamName}`;
  request.sequenceToken = (cacheKey in sequenceTokenCache) ? sequenceTokenCache[cacheKey] : null;
  console.log(`Putting ${request.logEvents.length} events to CWL.`)
  return cloudwatchlogs.putLogEvents(request)
    .promise()
    .then(response => {
      // if the call is successful, cache the next sequence token
      console.log(`Put succeeded, next token: ${response.nextSequenceToken}`);
      sequenceTokenCache[cacheKey] = response.nextSequenceToken;
    })
    .catch(err => {
      if (err.code == 'InvalidSequenceTokenException') {
        var correctSequenceToken = String(err).split(' ');
        correctSequenceToken = correctSequenceToken[correctSequenceToken.length - 1];
        console.log(`Sequence token invalid, correct token: ${correctSequenceToken}`);
        sequenceTokenCache[cacheKey] = correctSequenceToken;
        return exports.putLogEvents(cloudwatchlogs, request, sequenceTokenCache);
      } else {
        return prepareCloudWatchLogs(cloudwatchlogs, request.logGroupName, request.logStreamName)
          .then(token => {
            sequenceTokenCache[cacheKey] = token;
            return exports.putLogEvents(cloudwatchlogs, request, sequenceTokenCache)
          })
      }
    })
}


////
// deserialization and formatting
//
exports.formatLogEntry = function(logEntry) {
  return {
    timestamp: Date.parse(logEntry.timestamp),
    message: logEntry.textPayload != undefined ? logEntry.textPayload : logEntry.protoPayload,
  }
}


var getLogGroup = function(unformattedLogEntry) {
  return `/gcp/${unformattedLogEntry.resource.type}/${unformattedLogEntry.resource.labels.function_name}`;
}


var decode = function(data) {
  return JSON.parse(Buffer.from(data, 'base64').toString());
}


////
// AWS log group/stream preparation
//
function prepareCloudWatchLogs(cloudwatchlogs, logGroup, logStream) {

  var status = {
    logGroup: logGroup,
    logStream: logStream,
    logGroupExists: undefined,
    logStreamExists: undefined,
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

  return getUploadTokenIfPossible(status)
    .then(status => createLogGroupIfNeeded(status))
    .then(status => createLogStreamIfNeeded(status))
    .then(status => status.uploadToken)
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
    )
  }
  return recurse(request);
}
