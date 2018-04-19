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
    whitelisted_log_message_terms = os.environ["AIRBRAKE_WHITELISTED_LOG_MESSAGE_TERMS"]
    whitelisted_log_message_terms_regex_string = "|".join(whitelisted_log_message_terms.split())
    whitelisted_log_message_terms_regexp = re.compile(whitelisted_log_message_terms_regex_string, re.IGNORECASE)

    def __init__(self):
        self.report = {
            'other': 0,
            'errors': 0
        }

    def notify_stream(self, record_stream):
        for record in record_stream:
            if AirbrakeNotifier.notifiy(record):
                self.report['errors'] += 1
            else:
                self.report['other'] += 1
            yield record

    @staticmethod
    def notifiy(record):
        message = record['@message']
        log_group = record['@log_group']
        log_stream = record['logStream']
        if AirbrakeNotifier._is_message_appropriate_for_airbrake(message, log_group):
            airbrake_error = "'{0} {1} '@log_stream': {2}".format(log_group, message, log_stream)
            try:
                AirbrakeNotifier.airbrake_notifier.notify(str(airbrake_error))
                return True
            except Exception as e:
                logger.error("Airbrake notification failed!", e)
                pass
        return False

    @staticmethod
    def _is_message_appropriate_for_airbrake(message, log_group):
        if log_group not in AirbrakeNotifier.blacklisted_log_group_names_set and \
                AirbrakeNotifier.whitelisted_log_message_terms_regexp.search(message):
            return True
        return False
