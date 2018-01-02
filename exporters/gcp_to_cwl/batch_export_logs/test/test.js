var assert = require('assert');
var should = require('should');
var sinon = require('sinon');
var index = require('../index');

var sandbox = sinon.createSandbox();

describe('{de,}serialization', function() {

  const logEntry = {
    insertId: 'UUID4',
    labels: {
      execution_id: '1234567890'
    },
    logName: 'helloworld.log',
    receiveTimestamp: '2017-12-24T06:27:32.635872232Z',
    resource: {
      labels: {
        function_name: 'Fn1',
        project_id: 'cool-project',
        region: 'us-central1'
      },
      type: 'cloud_function'
    },
    severity: 'DEBUG',
    textPayload: 'Wed Apr 15 20:40:51 CEST 2015 Hello, world!',
    timestamp: '2015-04-15T18:40:56.000000000Z'
  };

  const logEntryString = JSON.stringify(logEntry);

  const pubSubEvent = {
    insertId: "000000-28daee0d-abbb-4d2a-8286-c1a3b61962e1",
    labels: {
      execution_id: "15338991883624",
    },
    logName: "helloworld.log",
    receiveTimestamp: "2017-12-24T06:27:38.851847956Z",
    resource: {
      labels: {
        function_name: "exportLogsPubSub",
        project_id: "human-cell-atlas-travis-test",
        region: "us-central1"
      },
    },
    type: "cloud_function",
    severity: "INFO",
    textPayload: new Buffer(logEntryString).toString('base64'),
    timestamp: '2015-04-15T18:40:56.000000000Z'
  };

  const pubSubEventString = JSON.stringify(pubSubEvent);

  const formattedLogEntry = {
    timestamp: 1514365325211,
    message: 'File blobs/aaaa.bbbb.cccc-d.eeee.ffff deleted.'
  };

  const formattedLogEntryString = JSON.stringify(formattedLogEntry);

  const bulkMessage = {
    data: new Buffer(formattedLogEntryString).toString('base64'),
    messageId: "16625951202671",
    publishTime: "2017-12-27T09:02:22.760Z"
  };

  const synchronousPullEnvelope = {
    receivedMessages: [
      {
        ackId: 'XkASTD4FRElTK0MLKlgRTgQhIT4wPkVTRFAGFixdRkhRNxkIaFEOT14jPzUgKEURCQgUBXx9cUFZdV1dGgdRDRlyfGd1Y10QAlRAVXxVWhENem1cVzlQCx9wdGF9bF0UBQVCVFb829CGk49vZho9XxJLLD5-NTBFQQ',
        message: bulkMessage,
      },
      {
        ackId: 'XkASTD4FRElTK0MLKlgRTgQhIT4wPkVTRFAGFixdRkhRNxkIaFEOT14jPzUgKEURCQgUBXx9cUFZdV1dGgdRDRlyfGd1Y10QAlRAVXxVXhENem1cVzlQCx9wdWZ9YlsaCQtEVFb829CGk49vZho9XxJLLD5-NTBFQQ',
        message: bulkMessage,
      }
    ]
  }

  it('should open a batch envelope', () => {
    assert.deepEqual(
      index.openSynchronousPullEnvelope(synchronousPullEnvelope),
      [
        [formattedLogEntry, formattedLogEntry],
        [
          synchronousPullEnvelope.receivedMessages[0].ackId,
          synchronousPullEnvelope.receivedMessages[1].ackId
        ],
      ]
    )
  });
});

describe('streamUntil', function() {
  it('should return the result if there is nothing next', function() {
      return index.streamUntil(
        Promise.resolve("initial"),
        function(response) {
          return [null, response + " + response processing"];
        }
      ).should.eventually.equal("initial + response processing");
  });

  it('should continue until there is nothing next', function () {
      var counter = 0
      return index.streamUntil(
        Promise.resolve("starting"),
        function(response) {
          counter += 1;
          return [counter < 2 ? Promise.resolve("continuing") : null, [counter, response]];
        }
      ).should.eventually.deepEqual([2, 'continuing']);
  });
});
