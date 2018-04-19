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
