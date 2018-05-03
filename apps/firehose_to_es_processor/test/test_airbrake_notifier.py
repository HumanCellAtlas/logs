import unittest
from lib.airbrake_notifier import AirbrakeNotifier


class TestFirehoseRecord(unittest.TestCase):

    def test_is_message_appropriate_for_airbrake(self):
        # whitelisted message term and non-blacklisted log group name
        message = "traceback: blah blah blah"
        log_group = "not_blacklisted"
        flag = AirbrakeNotifier._is_message_appropriate_for_airbrake(message, log_group)
        self.assertEqual(flag, True)

        # non whitelisted message term and non-blacklisted log group name
        message = "blah blah blah"
        log_group = "not_blacklisted"
        flag = AirbrakeNotifier._is_message_appropriate_for_airbrake(message, log_group)
        self.assertEqual(flag, False)

        # whitelisted message term and blacklisted log group name
        message = "traceback: blah blah blah"
        log_group = "/aws/cloudtrail/audit-and-data-access"
        flag = AirbrakeNotifier._is_message_appropriate_for_airbrake(message, log_group)
        self.assertEqual(flag, False)

        # non whitelisted message term and blacklisted log group name
        message = "blah blah blah"
        log_group = "/aws/cloudtrail/audit-and-data-access"
        flag = AirbrakeNotifier._is_message_appropriate_for_airbrake(message, log_group)
        self.assertEqual(flag, False)

    def test_string_blacklist(self):
        message = "traceback: blah blah blah"
        flag = AirbrakeNotifier._contains_blacklisted_string(message)
        self.assertEqual(flag, False)

        message = "blah blah Machine-readable error code blah blah"
        flag = AirbrakeNotifier._contains_blacklisted_string(message)
        self.assertEqual(flag, True)

    def test_report(self):
        record1 = {
            '@message': "traceback: blah blah blah",
            '@log_group': "not_blacklisted1",
            '@log_stream': 'some-stream'
        }
        record2 = {
            '@message': "hi!",
            '@log_group': "not_blacklisted1",
            '@log_stream': 'some-stream'
        }
        record3 = {
            '@message': "traceback: blah blah blah",
            '@log_group': "not_blacklisted2",
            '@log_stream': 'some-stream'
        }
        notifier = AirbrakeNotifier()
        for record in [record1, record1, record2, record3]:
            notifier.notify(record)
        report = notifier.report()
        self.assertEqual(len(report), 4)
        self.assertEqual(set(report), {
            ('not_blacklisted1', 'errors', 2),
            ('not_blacklisted1', 'total', 3),
            ('not_blacklisted2', 'errors', 1),
            ('not_blacklisted2', 'total', 1),
        })
