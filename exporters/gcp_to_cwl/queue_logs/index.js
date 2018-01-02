const PubSub = require(`@google-cloud/pubsub`);


/**
 * queueLogEntries Cloud Function.
 *
 * @param {object} event a timer event initiating the export
 * @param {function} callback a callback function
 */
exports.queueLogs = function (event, callback) {
  if (!event.data) callback(); // no data

  const logEntry = exports.decode(event.data.data);
  const topicName = exports.getTopicName(logEntry);

  if (logEntry.textPayload == undefined && logEntry.protoPayload == undefined) callback(); // no message data

  const formattedLogEntry = exports.formatLogEntry(logEntry);
  const dataBuffer = Buffer.from(JSON.stringify(formattedLogEntry));

  const pubsub = PubSub();
  const topic = pubsub.topic(topicName);
  const publisher = topic.publisher();

  return publisher.publish(dataBuffer)
    .then(result => logPublishSuccess(result, callback))
    .catch(err => {
      if (err && !notFound(err)) throw err
      return topic.create(function(err, topic, apiResponse) {
        if (err && !alreadyExists(err)) throw err
        publisher.publish(data).then(result => logPublishSuccess(result, callback))
      });
    });
}


exports.decode = function(data) {
  return JSON.parse(Buffer.from(data, 'base64').toString());
}


function notFound(err) {
  return String(err).indexOf('Resource not found') > -1;
}


function alreadyExists(err) {
  return String(err).indexOf('Resource already exists') > -1;
}


function logPublishSuccess(results, callback) {
    const messageId = results[0];
    console.log(`Message ${messageId} published.`);
    return callback();
}


exports.formatLogEntry = function(logEntry) {
  return {
    timestamp: Date.parse(logEntry.timestamp),
    message: logEntry.textPayload != undefined ? logEntry.textPayload : logEntry.protoPayload,
  }
}


exports.getTopicName = function(logEntry) {
  return `logs.${logEntry.resource.type}.${logEntry.resource.labels.function_name}`;
}