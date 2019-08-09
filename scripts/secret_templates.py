#!/usr/bin/env python
import boto3
import json

secret_templates = {
    'logs/_/gcp-credentials-logs-travis.json': dict(),
    'logs/_/config.json': {
        'account_id': 'DEFINE',
        'es_principal_emails': [],
        'es_principal_arns': [],
        'aws_profile': 'DEFINE',
        'aws_region': 'DEFINE',
        'cloudtrail_log_group_name': 'DEFINE',
        'deployment_stage': 'DEFINE',
        'es_domain_name': 'DEFINE',
        'gcp_logs_project_name': 'DEFINE',
        'travis_user': 'logs-travis',
        'cloudtrail_name': 'DEFINE',
        'gcp_region': 'DEFINE',
        'gcp_log_topic_subscription_name': 'DEFINE',
        'gcp_pubsub_authorized_service_accounts': [],
        'terraform_bucket': 'DEFINE'
    },
    'logs/_/cwl_to_slack.json': {
        'slack_alert_channel': 'DEFINE',
        'slack_webhooks': {
            'DEFINE_CHANNEL': 'DEFINE_URL'
        }
    },
    'logs/_/cwl_firehose_subscriber.json': {
        'blacklisted_log_groups': [
            'subscribertest',
            'test-log-group',
            '/aws/lambda/test_log_group',
            '/aws/lambda/Firehose-CWL-Processor',
            '/aws/kinesisfirehose/Kinesis-Firehose-ES',
            'API-Gateway-Execution-Logs'
        ]
    },
    'logs/_/firehose_to_es_processor.json': {
        'airbrake_blacklisted_log_group_names': [
            '/aws/cloudtrail/audit-and-data-access'
        ],
        'airbrake_whitelisted_log_message_terms': [
            'stacktrace',
            'traceback',
            'error',
            'exception',
            'critical'
        ],
        'airbrake_blacklisted_log_message_strings': [
            'Machine-readable error code',
            'validation_errors',
            'error_summary_metrics',
            'cannot find the current segment'
        ],
        'airbrake_enabled': True,
        'airbrake_api_key': 'DEFINE',
        'airbrake_project_id': 1010101,
        'airbrake_environment': 'DEFINE'
    },
    'logs/_/gcp_to_cwl.json': {
        'gcp_exporter_google_application_credentials': dict()
    },
    'logs/_/log_retention_policy_enforcer.json': {
        'log_retention_ttls': {
            '/aws/cloudtrail/audit-and-data-access': 731
        }
    }
}

secrets_client = boto3.client('secretsmanager')

secret_map = dict()
for name, json_as_dict in secret_templates.items():
    secrets_client.create_secret(
        Name=name,
        SecretString=json.dumps(json_as_dict)
    )
    print(f"PUT {name}")
