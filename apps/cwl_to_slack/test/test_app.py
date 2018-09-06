import unittest
from unittest.mock import patch
from app import handler


class TestApp(unittest.TestCase):
    def setUp(self):
        self.mock_secrets = {
            'SecretString': '{'
                            '"slack_alert_channel": "dcp-ops-alerts",'
                            '"slack_webhooks":{'
                                '"dcp-ops":"dcp_slack_url",'
                                '"upload-service":"upload_slack_url",'
                                '"dcp-ops-alerts":"dcp_ops_alert_slack_url"'
                            '}}'

        }

        self.mock_event_alarm = {
            'Records': [
                {
                    'Sns': {
                        'Message':
                            '{"AlarmName":"upload-staging",'
                            '"AlarmDescription":'
                                '"{ \\"slack_channel\\": \\"upload-service\\"}",'
                            '"NewStateValue":"ALARM",'
                            '"NewStateReason":"words words words",'
                            '"OldStateValue":"OK"'
                            '}'
                    }
                }
            ]
        }
        self.mock_event_no_channel_ok = {
            'Records': [
                {
                    'Sns': {
                        'Message':
                            '{"AlarmName":"upload-staging",'
                            '"AlarmDescription":'
                            '"{}",'
                            '"NewStateValue":"OK",'
                            '"NewStateReason":"words words words",'
                            '"OldStateValue":"ALARM"'
                            '}'
                    }
                }
            ]
        }

        self.mock_attachment_alarm = {
            'attachments': [
                {'fallback': '<https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarm:alarmFilter=ANY;'
                             'name=upload-staging|upload-staging> State is now ALARM: \n words words words',
                 'title': 'upload-staging',
                 'title_link': 'https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarm:alarmFilter=ANY;'
                               'name=upload-staging',
                 'text': 'State is now ALARM: \n words words words',
                 'color': 'danger'}
            ]
        }
        self.mock_attachment_ok = {
            'attachments': [
                {'fallback': '<https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarm:alarmFilter=ANY;'
                             'name=upload-staging|upload-staging> State is now OK: \n words words words',
                 'title': 'upload-staging',
                 'title_link': 'https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarm:alarmFilter'
                               '=ANY;name=upload-staging',
                 'text': 'State is now OK: \n words words words',
                 'color': 'good'
                 }
            ]
        }

    @patch('app.get_secret')
    @patch('app.post_message_to_url')
    def test_posts_alarm_to_correct_slack_channel(self, mock_post_req, mock_get_secret):
        mock_get_secret.return_value = self.mock_secrets
        handler(self.mock_event_alarm, 'no_context')
        mock_post_req.assert_called_with('upload_slack_url', self.mock_attachment_alarm)

    @patch('app.get_secret')
    @patch('app.post_message_to_url')
    def test_posts_to_dcp_ops_alert_if_channel_not_specified(self, mock_post_req, mock_get_secret):
        mock_get_secret.return_value = self.mock_secrets
        handler(self.mock_event_no_channel_ok, 'no_context')
        mock_post_req.assert_called_with('dcp_ops_alert_slack_url', self.mock_attachment_ok)
