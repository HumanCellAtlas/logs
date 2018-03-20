import json
import typing
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.proto import pubsub_pb2


class SynchronousPullClient:

    def __init__(self, project_id, subscription_name):
        self.client = pubsub_v1.SubscriberClient()
        self.subscription = self.client.subscription_path(project_id, subscription_name)

    @staticmethod
    def _open_pull_envelope(envelope) -> typing.Tuple[typing.List[dict], typing.List[str]]:
        ack_ids = [m.ack_id for m in envelope.received_messages]
        messages = [
            json.loads(str(m.message.data, 'utf-8'))
            for m in envelope.received_messages
        ]
        assert(len(ack_ids) == len(messages))
        return messages, ack_ids

    def pull(self, batch_size) -> typing.Tuple[typing.List[dict], typing.List[str]]:
        request = pubsub_pb2.PullRequest(
            subscription=self.subscription,
            max_messages=batch_size,
            return_immediately=True)
        response = self.client.api._pull(request)
        return self._open_pull_envelope(response)

    def ack(self, ack_ids):
        self.client.acknowledge(self.subscription, ack_ids)

    def to_generator(self, batch_size):
        low_poll_count = 0
        while low_poll_count < 2:
            messages, ack_ids = self.pull(batch_size)
            if len(messages) < batch_size:
                low_poll_count += 1
            else:
                low_poll_count = 0

            if len(messages) > 0:
                yield messages
                self.ack(ack_ids)

