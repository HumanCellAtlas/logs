#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This AWS Lambda function allowed to delete the old Elasticsearch index
"""

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import create_credential_resolver
from botocore.session import get_session
from botocore.vendored.requests import Session
from retrying import retry
import sys
if sys.version_info[0] == 3:
    from urllib.request import quote
else:
    from urllib import quote
import datetime
import json
import os
import yaml
import domovoi


class ESException(Exception):
    """Exception capturing status_code from Client Request"""
    status_code = 0
    payload = ""

    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        Exception.__init__(self,
                           "ESException: status_code={}, payload={}".format(
                               status_code, payload))


class ESCleanup(object):

    name = "lambda_es_cleanup"

    def __init__(self, event, context, cluster_config):
        """Main Class init

        Args:
            event (dict): AWS Cloudwatch Scheduled Event
            context (object): AWS running context
        """
        self.report = []
        self.event = event
        self.context = context

        self.cfg = {}
        self.cfg["es_endpoint"] = cluster_config.get('endpoint')
        self.cfg["index"] = [index.get("prefix") for index in cluster_config.get('indices')]

        self.cfg["index_format"] = cluster_config.get('index_format')
        # Index cutoff definition, remove older than this date
        self.cfg["earliest_to_keep"] = datetime.date.today() - datetime.timedelta(days=int(cluster_config.get('days')))

        if not self.cfg["es_endpoint"]:
            raise Exception("[es_endpoint] OS variable is not set")

    @retry(wait_fixed=2000, stop_max_attempt_number=3)
    def send_to_es(self, path, method="GET", payload={}):
        """Low-level POST data to Amazon Elasticsearch Service generating a Sigv4 signed request

        Args:
            path (str): path to send to ES
            method (str, optional): HTTP method default:GET
            payload (dict, optional): additional payload used during POST or PUT

        Returns:
            dict: json answer converted in dict

        Raises:
            #: Error during ES communication
            ESException: Description
        """
        if not path.startswith("/"):
            path = "/" + path

        es_region = self.cfg["es_endpoint"].split(".")[1]

        req = AWSRequest(
            method=method,
            url="https://%s%s?pretty&format=json" % (self.cfg["es_endpoint"], quote(path)),
            data=payload,
            headers={'Host': self.cfg["es_endpoint"]})
        credential_resolver = create_credential_resolver(get_session())
        credentials = credential_resolver.load_credentials()
        SigV4Auth(credentials, 'es', es_region).add_auth(req)

        preq = req.prepare()
        session = Session()
        res = session.send(preq)
        session.close()
        if res.status_code >= 200 and res.status_code <= 299:
            return json.loads(res.content)
        else:
            raise ESException(res.status_code, res._content)

    def delete_index(self, index_name):
        """ES DELETE specific index

        Args:
            index_name (str): Index name

        Returns:
            dict: ES answer
        """
        return self.send_to_es(index_name, "DELETE")

    def create_index(self, index_name):
        """ES CREATE specific index

        Args:
            index_name (str): Index name

        Returns:
            dict: ES answer
        """
        return self.send_to_es(index_name, "PUT")

    def get_indices(self, filter_prefix=None):
        """ES Get indices

        Returns:
            list: ES answer
        """
        indices = self.send_to_es("/_cat/indices")
        if filter_prefix:
            return [i for i in indices if i['index'].startswith(filter_prefix)]
        else:
            return indices

    def should_delete_index(self, index):
        """Evaluate index for deletion

        Args:
            index (dict): Index

        Returns:
            boolean: boolean for whether index should be deleted
        """
        should_delete = False
        index_name = '-'.join(word for word in index["index"].split("-")[:-1])
        index_date = index["index"].split("-")[-1]
        # TODO: fix this bit
        if index_name in self.cfg["index"] or "all" in self.cfg["index"]:
            if index_date <= self.cfg["earliest_to_keep"].strftime(self.cfg["index_format"]):
                should_delete = True
        return should_delete

    def manage_indices(self):
        """ES Get indices

        Returns:
            list: ES answer
        """
        for index in self.get_indices():
            index_name = index["index"]
            if self.should_delete_index(index):
                print("Deleting index: %s" % index_name)
                self.delete_index(index_name)
        return self.get_indices()


app = domovoi.Domovoi()


@app.scheduled_function("rate(12 hours)")
def handler(event, context):
    """Main Lambda function
    """

    with open(os.environ['ES_IDX_MANAGER_SETTINGS'], 'r') as config_file:
        config = yaml.load(config_file)

        for cluster_config in config:

            es = ESCleanup(event, context, cluster_config)
            es.manage_indices()
