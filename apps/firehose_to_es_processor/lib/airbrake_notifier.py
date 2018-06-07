import os
import re
import logging
from airbrake.notifier import Airbrake

from .secrets import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AirbrakeNotifier:

    MAX_NOTIFICATIONS = 50
    airbrake_notifier = Airbrake(project_id=config['airbrake_project_id'], api_key=config['airbrake_api_key'])
    blacklisted_log_group_names = set(config['airbrake_blacklisted_log_group_names'])
    blacklisted_log_message_strings_regex = re.compile('|'.join(config["airbrake_blacklisted_log_message_strings"]))
    whitelisted_log_message_terms_regex_string = "|".join(config['airbrake_whitelisted_log_message_terms'])
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
        if log_group not in AirbrakeNotifier.blacklisted_log_group_names and \
                AirbrakeNotifier.whitelisted_log_message_terms_regexp.search(message):
            return True
        return False

    @staticmethod
    def _contains_blacklisted_string(message):
        if AirbrakeNotifier.blacklisted_log_message_strings_regex.search(message):
            return True
        return False
