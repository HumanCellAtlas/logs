import json
import os
from flask import current_app, Flask
from google.cloud import pubsub_v1

app = Flask(__name__)

PROJECT_ID = os.environ['GCLOUD_PROJECT']
LOG_TOPIC_PREFIX = f"projects/{PROJECT_ID}/topics/logs."

@app.route('/watch', methods=['GET'])
def get():
    publisher = pubsub_v1.PublisherClient()
    subscription_names = [
        s.name
        for s in publisher.list_subscriptions(publisher.project_path(PROJECT_ID))
        if s.name.startswith(LOG_TOPIC_PREFIX)
    ]
    for subscription_name in subscription_names:
        topic_path = publisher.topic_path(PROJECT_ID, 'timer-topic')
        payload = JSON.dumps({'projectName': PROJECT_ID, 'subscriptionName': subscription_name})
        publisher.publish(, topic_name.encode('utf-8'))
        print(">> notified timer-topic of: " + topic_name)
    return 'OK', 200
