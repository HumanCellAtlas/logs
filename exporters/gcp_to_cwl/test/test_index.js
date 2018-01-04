var { Readable } = require('stream');
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

  const formattedLogEntry = {
    timestamp: 1429123256000,
    message: 'Wed Apr 15 20:40:51 CEST 2015 Hello, world!'
  };

  const formattedLogEntryString = JSON.stringify(formattedLogEntry);

  it('should format log entries', () => {
    assert.deepEqual(index.formatLogEntry(logEntry), formattedLogEntry);
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
