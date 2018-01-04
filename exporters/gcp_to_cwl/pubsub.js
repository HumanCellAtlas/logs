const google = require('googleapis');

// TODO smoke test
exports.SynchronousPullClient = function(options) {
    this.hostname = 'pubsub.googleapis.com';
    this.projectId = options.projectId;
    this.subscription = options.subscription;
}


exports.SynchronousPullClient.prototype.auth = function() {
  return new Promise(function(resolve, reject) {
    google.auth.getApplicationDefault(function(err, authClient, projectId) {
        if (err) {
            reject(err);
            return;
        }
        if (authClient.createScopedRequired
            && authClient.createScopedRequired()
           ) {
            const scopes = [
                'https://www.googleapis.com/auth/cloud-platform',
                'https://www.googleapis.com/auth/pubsub',
            ];
            authClient = authClient.createScoped(scopes);
        }

        resolve(authClient);
    });
  });
}

exports.SynchronousPullClient.prototype.queryPath = function(operation) {
    return `v1/projects/${this.projectId}/subscriptions/${this.subscription}:${operation}`
}

exports.SynchronousPullClient.prototype.pull = function(size, callback) {
  var postData = {returnImmediately: false, maxMessages: size};
  const options = {
    url: `https://${this.hostname}/${this.queryPath('pull')}`,
    method: 'POST',
    json: true,
    body: postData,
  }
  return this.auth().then(authClient => {
    return authClient.request(options, function(err, body, response) {
      if (!err) return callback(body)
      throw err
    });
  });
}

exports.SynchronousPullClient.prototype.ack = function(ackIds, callback) {
  if (ackIds.length == 0) return callback({});
  var postData = {ackIds: ackIds};
  const options = {
    url: `https://${this.hostname}/${this.queryPath('acknowledge')}`,
    method: 'POST',
    json: true,
    body: postData,
  }
  return this.auth().then(authClient => {
    return authClient.request(options, function(err, body, response) {
      if (!err) return callback(body)
      else throw err
    });
  });
}


exports.SynchronousPullClient.prototype.stream = function(n, processCallback, endCallback) {
  return this.pull(n, body => {
    var [messages, ackIds] = exports.openSynchronousPullEnvelope(body);
    return processCallback(messages)
      .then(callbackResult => this.ack(ackIds, responseBody => callbackResult))
      .then(ackResult => {
        if (messages.length == n) {
          return this.stream(n, processCallback, endCallback);
        }
        return endCallback();
      })
  })
}


var decode = function(data) {
  return JSON.parse(Buffer.from(data, 'base64').toString());
}


exports.openSynchronousPullEnvelope = function(envelope) {
  if (envelope.receivedMessages == undefined) return [[], []];
  var ackIds = envelope.receivedMessages.map(m => m.ackId);
  var messages = envelope.receivedMessages.map(m => decode(m.message.data));
  return [messages, ackIds];
}