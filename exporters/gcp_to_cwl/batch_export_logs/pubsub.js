const google = require('googleapis');

// TODO smoke test
exports.SynchronousPullClient = function(projectId, subscription) {
    this.hostname = 'pubsub.googleapis.com';
    this.projectId = projectId;
    this.subscription = subscription;
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