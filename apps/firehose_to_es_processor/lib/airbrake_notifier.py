import os
import re
import logging
from airbrake.notifier import Airbrake

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AirbrakeNotifier:

    MAX_NOTIFICATIONS = 50
    airbrake_notifier = Airbrake(project_id=os.environ["AIRBRAKE_PROJECT_ID"], api_key=os.environ["AIRBRAKE_API_KEY"])
    blacklisted_log_group_names = os.environ["AIRBRAKE_BLACKLISTED_LOG_GROUP_NAMES"]
    blacklisted_log_group_names_set = set(blacklisted_log_group_names.split())
    blacklisted_log_message_strings_regex = re.compile('|'.join(os.environ["AIRBRAKE_BLACKLISTED_LOG_MESSAGE_STRINGS"].split(',')))
    whitelisted_log_message_terms = os.environ["AIRBRAKE_WHITELISTED_LOG_MESSAGE_TERMS"]
    whitelisted_log_message_terms_regex_string = "|".join(whitelisted_log_message_terms.split(','))
    whitelisted_log_message_terms_regexp = re.compile(whitelisted_log_message_terms_regex_string, re.IGNORECASE)

    def __init__(self):
        self._report = dict()
        self._total_errors = 0
        self._airbrake_rate_limited = False
        self.error_report = dict()

    def report(self):
        results = []
        for log_group, subcounts in self._report.items():
            for message_type, count in subcounts.items():
                results += [(log_group, message_type, count)]
        return results

    def notify_on_stream(self, log_event_stream):
        for log_event in log_event_stream:
            self.notify(log_event)
            yield log_event

    def notify(self, log_event):
        message = log_event['@message']
        log_group = log_event['@log_group']
        log_stream = log_event['@log_stream']
        error_str = None
        if AirbrakeNotifier._is_message_appropriate_for_airbrake(message, log_group) and \
                not AirbrakeNotifier._contains_blacklisted_string(message):
            error_str = "'{0} {1} '@log_stream': {2}".format(log_group, message, log_stream)
            try:
                if not self._airbrake_rate_limited and self._total_errors < AirbrakeNotifier.MAX_NOTIFICATIONS:
                    AirbrakeNotifier.airbrake_notifier.notify(error_str)
            except Exception as e:
                message = str(e)
                if message.startswith('420 Client Error'):
                    self._airbrake_rate_limited = True
                else:
                    logger.error("Airbrake notification failed! {}".format(message))
        self._observe(log_group, error_str)

    def _observe(self, log_group, error_str):
        if log_group not in self._report:
            self._report[log_group] = {
                'errors': 0,
                'total': 0
            }
        if error_str:
            if error_str not in self.error_report:
                self.error_report[error_str] = 1
            else:
                self.error_report[error_str] += 1
            self._report[log_group]['errors'] += 1
            self._total_errors += 1
        self._report[log_group]['total'] += 1

    @staticmethod
    def _is_message_appropriate_for_airbrake(message, log_group):
        if log_group not in AirbrakeNotifier.blacklisted_log_group_names_set and \
                AirbrakeNotifier.whitelisted_log_message_terms_regexp.search(message):
            return True
        return False

    @staticmethod
    def _contains_blacklisted_string(message):
        if AirbrakeNotifier.blacklisted_log_message_strings_regex.search(message):
            return True
        return False
