import os
import re
import logging
from airbrake.notifier import Airbrake

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AirbrakeNotifier:

    airbrake_notifier = Airbrake(project_id=os.environ["AIRBRAKE_PROJECT_ID"], api_key=os.environ["AIRBRAKE_API_KEY"])
    blacklisted_log_group_names = os.environ["AIRBRAKE_BLACKLISTED_LOG_GROUP_NAMES"]
    blacklisted_log_group_names_set = set(blacklisted_log_group_names.split())
    blacklisted_log_message_strings = os.environ["AIRBRAKE_BLACKLISTED_LOG_MESSAGE_STRINGS"].split(',')
    whitelisted_log_message_terms = os.environ["AIRBRAKE_WHITELISTED_LOG_MESSAGE_TERMS"]
    whitelisted_log_message_terms_regex_string = "|".join(whitelisted_log_message_terms.split(','))
    whitelisted_log_message_terms_regexp = re.compile(whitelisted_log_message_terms_regex_string, re.IGNORECASE)

    def __init__(self):
        self._report = dict()
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
        is_error = False
        if AirbrakeNotifier._is_message_appropriate_for_airbrake(message, log_group) and \
                not AirbrakeNotifier._contains_blacklisted_string(message):
            airbrake_error = "'{0} {1} '@log_stream': {2}".format(log_group, message, log_stream)
            if airbrake_error not in self.error_report:
                self.error_report[airbrake_error] = 1
            else:
                self.error_report[airbrake_error] += 1
            is_error = True
            try:
                AirbrakeNotifier.airbrake_notifier.notify(str(airbrake_error))
            except Exception as e:
                message = str(e)
                if not message.startswith('420 Client Error'):
                    logger.error("Airbrake notification failed! {}".format(message))
        self._observe(log_group, is_error)

    def _observe(self, log_group, is_error):
        if log_group not in self._report:
            self._report[log_group] = {
                'errors': 0,
                'total': 0
            }
        if is_error:
            self._report[log_group]['errors'] += 1
        self._report[log_group]['total'] += 1

    @staticmethod
    def _is_message_appropriate_for_airbrake(message, log_group):
        if log_group not in AirbrakeNotifier.blacklisted_log_group_names_set and \
                AirbrakeNotifier.whitelisted_log_message_terms_regexp.search(message):
            return True
        return False

    @staticmethod
    def _contains_blacklisted_string(message):
        for blacklisted_string in AirbrakeNotifier.blacklisted_log_message_strings:
            if blacklisted_string in message:
                return True
        return False
