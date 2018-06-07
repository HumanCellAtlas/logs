#!/usr/bin/env python
import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../domovoilib'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import unittest
import json
import uuid
from pubsub import SynchronousPullClient
from google.cloud import pubsub_v1
from contextlib import contextmanager
from secrets import config


class TestSynchronousPullClient(unittest.TestCase):

    @staticmethod
    def _msg(i):
        return "{\"iter\": " + str(i) + "}"

    @classmethod
    @contextmanager
    def test_context_and_client(cls):
        # params
        project_id = config['gcp_exporter_google_application_credentials']['project_id']
        topic_path = f"projects/{project_id}/topics/topic.{str(uuid.uuid4())}"
        subscription_name = f"subscription.{str(uuid.uuid4())}"
        subscription_path = f"projects/{project_id}/subscriptions/{subscription_name}"

        # clients
        pull_client = SynchronousPullClient(project_id, subscription_name)
        publish_client = pubsub_v1.PublisherClient()
        subscriber_client = pubsub_v1.SubscriberClient()

        try:
            publish_client.api.create_topic(topic_path)
            subscriber_client.api.create_subscription(subscription_path, topic_path)
            for i in range(100):
                publish_client.publish(topic_path, bytes(cls._msg(i), 'utf-8'))

            yield pull_client
        finally:
            publish_client.api.delete_topic(topic_path)

    def test_pull_and_ack(self):
        batch_size = 50
        with self.test_context_and_client() as pull_client:
            messages, ack_ids = pull_client.pull(batch_size)
            self.assertEqual(len(messages), batch_size)
            for i, message in enumerate(messages):
                self.assertEqual(message, json.loads(self._msg(i)))
            pull_client.ack(ack_ids)
            messages, ack_ids = pull_client.pull(batch_size)
            self.assertEqual(len(messages), batch_size)
            for i, message in enumerate(messages):
                self.assertEqual(message, json.loads(self._msg(i + batch_size)))
            pull_client.ack(ack_ids)

    def test_to_generator(self):
        with self.test_context_and_client() as pull_client:
            num_batches = 0
            i = 0
            for messages in pull_client.to_generator(25):
                num_batches += 1
                for message in messages:
                    self.assertEqual(message, json.loads(self._msg(i)))
                    i += 1
            self.assertEqual(num_batches, 4)
            self.assertEqual(i, 100)


if __name__ == '__main__':
    unittest.main()
