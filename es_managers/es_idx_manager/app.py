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
import sys
if sys.version_info[0] == 3:
    from urllib.request import quote
else:
    from urllib import quote
import datetime
import json
import time
import os
import yaml

import domovoi

class ES_Exception(Exception):
    """Exception capturing status_code from Client Request"""
    status_code = 0
    payload = ""

    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        Exception.__init__(self,
                           "ES_Exception: status_code={}, payload={}".format(
                               status_code, payload))


class ES_Cleanup(object):

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

        self.cfg["delete_after"] = cluster_config.get('days')
        self.cfg["es_max_retry"] = 3
        self.cfg["index_format"] = cluster_config.get('index_format')
        self.cfg["sns_alert"] = cluster_config.get('sns_alert', "")

        if not self.cfg["es_endpoint"]:
            raise Exception("[es_endpoint] OS variable is not set")

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
            ES_Exception: Description
        """
        if not path.startswith("/"):
            path = "/" + path

        es_region = self.cfg["es_endpoint"].split(".")[1]

        # send to ES with exponential backoff
        retries = 0
        while retries < int(self.cfg["es_max_retry"]):
            if retries > 0:
                seconds = (2**retries) * .1
                # print('Waiting for %.1f seconds', seconds)
                time.sleep(seconds)

            req = AWSRequest(
                method=method,
                url="https://%s%s?pretty&format=json" % (self.cfg["es_endpoint"], quote(path)),
                data=payload,
                headers={'Host': self.cfg["es_endpoint"]})
            credential_resolver = create_credential_resolver(get_session())
            credentials = credential_resolver.load_credentials()
            SigV4Auth(credentials, 'es', es_region).add_auth(req)

            try:
                preq = req.prepare()
                session = Session()
                res = session.send(preq)
                if res.status_code >= 200 and res.status_code <= 299:
                    # print("%s %s" % (res.status_code, res.content))
                    return json.loads(res.content)
                else:
                    raise ES_Exception(res.status_code, res._content)

            except ES_Exception as e:
                if (e.status_code >= 500) and (e.status_code <= 599):
                    retries += 1  # Candidate for retry
                else:
                    raise  # Stop retrying, re-raise exception

    def send_error(self, msg):
        """Send SNS error
        
        Args:
            msg (str): error string
        
        Returns:
            None
        """
        _msg = "[%s][%s] %s" % (self.name, self.cur_account, msg)
        print(_msg)
        if self.cfg["sns_alert"] != "":
            sns_region = self.cfg["sns_alert"].split(":")[4]
            sns = boto3.client("sns", region_name=sns_region)
            response = sns.publish(
                TopicArn=self.cfg["sns_alert"], Message=_msg)

    def delete_index(self, index_name):
        """ES DELETE specific index
        
        Args:
            index_name (str): Index name
        
        Returns:
            dict: ES answer
        """
        return self.send_to_es(index_name, "DELETE")

    def get_indices(self):
        """ES Get indices
        
        Returns:
            dict: ES answer
        """
        return self.send_to_es("/_cat/indices")

app = domovoi.Domovoi()
@app.scheduled_function("rate(12 hours)")
def handler(event, context):
    """Main Lambda function
    """

    with file(os.environ['ES_IDX_MANAGER_SETTINGS'], 'r') as config_file:
        config = yaml.load(config_file)

    for cluster_config in config:

        es = ES_Cleanup(event, context, cluster_config)
        # Index cutoff definition, remove older than this date
        earliest_to_keep = datetime.date.today() - datetime.timedelta(
            days=int(es.cfg["delete_after"]))
        for index in es.get_indices():

            if index["index"] == ".kibana":
                # ignore .kibana index
                continue

            idx_name = '-'.join(word for word in index["index"].split("-")[:-1])
            idx_date = index["index"].split("-")[-1]

            if idx_name in es.cfg["index"] or "all" in es.cfg["index"]:

                if idx_date <= earliest_to_keep.strftime(es.cfg["index_format"]):
                    print("Deleting index: %s" % index["index"])
                    es.delete_index(index["index"])
