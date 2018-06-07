'use strict';

/**
 * Follow these steps to configure the webhook in Slack:
 *
 *   1. Navigate to https://<your-team-domain>.slack.com/services/new
 *
 *   2. Search for and select "Incoming WebHooks".
 *
 *   3. Choose the default channel where messages will be sent and click "Add Incoming WebHooks Integration".
 *
 *   4. Copy the webhook URL from the setup instructions and use it in the next section.
*/

const url = require('url');
const https = require('https');
var AWS = require('aws-sdk'),
    endpoint = "https://secretsmanager.us-east-1.amazonaws.com",
    secretName = "logs/_/cwl_to_slack.json",
    secret;

const region = process.env.region;

// Create a Secrets Manager client
var secrets_client = new AWS.SecretsManager({
    endpoint: endpoint,
    region: region
});

// The Slack webhook url and channel to send a message to stored in the slackChannel environment variable
var hookUrl = undefined;
var slackChannel = undefined;

const baseUrl = 'https://console.aws.amazon.com/cloudwatch/home?region=' + region + '#alarm:alarmFilter=ANY;name=';

function postMessage(message, callback) {
    const body = JSON.stringify(message);
    const options = url.parse(hookUrl);
    options.method = 'POST';
    options.headers = {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
    };

    const postReq = https.request(options, (res) => {
        const chunks = [];
        res.setEncoding('utf8');
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () => {
            if (callback) {
                callback({
                    body: chunks.join(''),
                    statusCode: res.statusCode,
                    statusMessage: res.statusMessage,
                });
            }
        });
        return res;
    });

    postReq.write(body);
    postReq.end();
}

function processEvent(event, callback) {
    const message = JSON.parse(event.Records[0].Sns.Message);

    const alarmName = message.AlarmName;
    //var oldState = message.OldStateValue;
    const newState = message.NewStateValue;
    const reason = message.NewStateReason;

    const slackMessage = {
        channel: slackChannel,
        text: `<${baseUrl}${alarmName}|${alarmName}> state is now ${newState}: ${reason}`,
    };

    postMessage(slackMessage, (response) => {
        if (response.statusCode < 400) {
            console.info('Message posted successfully');
            callback(null);
        } else if (response.statusCode < 500) {
            console.error(`Error posting message to Slack API: ${response.statusCode} - ${response.statusMessage}`);
            callback(null);  // Don't retry because the error is due to a problem with the request
        } else {
            // Let Lambda retry
            callback(`Server error when processing message: ${response.statusCode} - ${response.statusMessage}`);
        }
    });
}


exports.handler = (event, context, callback) => {
    if (hookUrl !== undefined && slackChannel !== undefined) {
        // Container reuse, simply process the event with the key in memory
        processEvent(event, callback);
    } else {
        secrets_client.getSecretValue({SecretId: secretName}, function(err, data) {
            if(err) {
                if(err.code === 'ResourceNotFoundException')
                    console.log("The requested secret " + secretName + " was not found");
                else if(err.code === 'InvalidRequestException')
                    console.log("The request was invalid due to: " + err.message);
                else if(err.code === 'InvalidParameterException')
                    console.log("The request had invalid params: " + err.message);
                else
                    throw err;
            } else {
                secret = JSON.parse(data.SecretString);
                hookUrl = secret.slack_webhook_url.startsWith('https://') ? secret.slack_webhook_url : `https://${secret.slack_webhook_url}`;
                slackChannel = secret.slack_alert_channel;
            }

            processEvent(event, callback);
        });
    }
};