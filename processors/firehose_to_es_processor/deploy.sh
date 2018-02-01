#!/usr/bin/env bash
export SERVICE=lambda

# create export role and policy
aws iam create-role \
--role-name firehose-cwl-log-processor \
--assume-role-policy-document "$(envsubst_to_str config/iam-policy-templates/assume_role.json '$SERVICE')" \
2> /dev/null \
|| echo "firehose-cwl-log-processor IAM role already exists."

aws iam put-role-policy \
--role-name firehose-cwl-log-processor \
--policy-name ProcessCWLFromFirehose \
--policy-document file://`pwd`/config/iam-policy-templates/lambda_firehose_execution.json \
2> /dev/null \
|| echo "Policy for ${ELK_EXPORT_ROLE_NAME} already exists."

aws lambda create-function \
--cli-input-json "$(envsubst_to_str config/iam-policy-templates/firehose-cwl-log-processor-lambda-deployment.json '$ES_ENDPOINT $FIREHOSE_CWL_ROLE_ARN')" \
2> /dev/null \
|| echo "Lambda function already exists!"

aws lambda add-permission \
--cli-input-json "$(envsubst_to_str config/iam-policy-templates/lambda_permission.json '$ACCOUNT_ID')" \
2> /dev/null \
|| echo "Permission already exists!"
