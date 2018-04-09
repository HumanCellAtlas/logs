import datetime
from botocore.credentials import create_credential_resolver
from botocore.session import get_session
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
from requests_aws4auth import AWS4Auth
import os
from retrying import retry


class ESClient():
    def __init__(self):
        self.es_endpoint = os.environ["ES_ENDPOINT"]
        credential_resolver = create_credential_resolver(get_session())
        credentials = credential_resolver.load_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', 'es', session_token=credentials.token)
        self.es = Elasticsearch(hosts=[{'host': self.es_endpoint, 'port': 443}], http_auth=awsauth, use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def create_cwl_day_index(self, prefix="cwl"):
        """ES CREATE specific index

        Args:
            index_name (str): Index name

        Returns:
            dict: ES answer
        """
        request_body = {
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 0
            }
        }
        index_name = self._format_today_index_name(prefix)
        if not self.es.indices.exists(index_name):
            self.es.indices.create(index=index_name, body=request_body)

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def delete_index(self, index_name):
        self.es.indices.delete(index=index_name)

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def bulk_post(self, payload, prefix="cwl"):
        index_name = self._format_today_index_name(prefix)
        helpers.bulk(self.es, payload, index=index_name, doc_type='fromFirehose')

    def _format_today_index_name(self, prefix):
        index_format = "%Y-%m-%d"
        today_index_name = prefix + "-" + datetime.datetime.today().strftime(index_format)
        return today_index_name