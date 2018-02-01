#!/usr/bin/env bash
set -e

##
# helper functions
#
TEMP_FILES=()

list_temp_files() {
  echo -n "${TEMP_FILES[@]}"
}

add_temp_file() {
  TEMP_FILES+=($1)
}

envsubst_to_str() {
    echo -n "$(cat ${1} | envsubst "${2}" | sed s/\"/\\\"/g)"
}

START_DIR=`pwd`

trap "{ rm -rf \$(list_temp_files); cd $START_DIR; }" EXIT SIGINT SIGTERM

status_report() {
  SYSTEM="$1"
  RETURN_VAL="$2"
  RESULT="$3"
  if [[ "$status_val" -eq 0 ]]; then
    echo "${SYSTEM} configuration successful:"
    echo "$RESULT"
  else
    echo "${SYSTEM} configuration failed!"
    exit 1
  fi
}

##
# global config
#
SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


##
# AWS CloudTrail configuration
#
setup_cloudtrail() {
  export LOG_GROUP_NAME=${CLOUDTRAIL_LOG_GROUP_NAME}

  aws cloudtrail create-trail \
    --name ${CLOUDTRAIL_NAME} \
    --s3-bucket-name ${ACCOUNT_ID}-cloudtrail \
    2> /dev/null \
    || echo "Instance of CloudTrail with that name already exists."

  aws iam create-role \
    --role-name ${CLOUDTRAIL_ROLE_NAME} \
    --assume-role-policy-document file://`pwd`/config/iam-policy-templates/assume_role.json \
    2> /dev/null \
    || echo "CloudTrail IAM role already exists."

  CLOUDTRAIL_ROLE_ARN=$(aws iam get-role \
    --role-name logging-aws-cloudtrail | jq -r '.Role.Arn')

  aws logs create-log-group \
    --log-group-name ${LOG_GROUP_NAME} \
    2> /dev/null \
    || echo "CloudTrail audit group already exits."

  export LOG_GROUP_ARN=$(aws logs describe-log-groups \
    | jq -r ".logGroups[] | select(.logGroupName == \"${CLOUDTRAIL_LOG_GROUP_NAME}\") | .arn")

  aws iam put-role-policy \
    --role-name ${CLOUDTRAIL_ROLE_NAME} \
    --policy-name cloudtrail-policy \
    --policy-document "$(envsubst_to_str config/iam-policy-templates/role.json '$REGION $LOG_GROUP_NAME $ACCOUNT_ID')"

  RESULT=$(aws cloudtrail update-trail \
    --name ${CLOUDTRAIL_NAME} \
    --cloud-watch-logs-log-group-arn ${LOG_GROUP_ARN} \
    --cloud-watch-logs-role-arn ${CLOUDTRAIL_ROLE_ARN})

  status_report "CloudTrail" $? "$RESULT"
}


##
# ElasticSearch
#
setup_ELK() {
  export SERVICE=lambda

  # create elasticsearch access policies
  export IP_ADDRESS_ARRAY="\"$(curl http://checkip.amazonaws.com/)\""

  # create domain
  ES_DOMAIN_RESULT=$(aws es create-elasticsearch-domain \
    --domain-name ${ES_DOMAIN_NAME} \
    --elasticsearch-version 5.5 \
    --elasticsearch-cluster-config InstanceType=m3.xlarge.elasticsearch,InstanceCount=2 \
    --ebs-options EBSEnabled=true,VolumeType=gp2,VolumeSize=512 \
    --access-policies "$(envsubst_to_str config/iam-policy-templates/es-access.json '$IP_ADDRESS_ARRAY $REGION $ACCOUNT_ID')") \

  status_report "ELK Stack" $? "$ES_DOMAIN_RESULT"
}

setup_kinesis_firehose_stream() {
  export SERVICE=firehose

  aws iam create-role \
    --role-name ${FIREHOSE_ROLE_NAME} \
    --assume-role-policy-document "$(envsubst_to_str config/iam-policy-templates/assume_role.json '$SERVICE')" \
    2> /dev/null \
    || echo "KINESIS FIREHOSE ES IAM role already exists."

  aws iam put-role-policy \
    --role-name ${FIREHOSE_ROLE_NAME} \
    --policy-name FirehoseES \
    --policy-document file://`pwd`/config/iam-policy-templates/firehose-to-es.json \
    2> /dev/null \
    || echo "Policy for ${FIREHOSE_ROLE_NAME} already exists."

  aws firehose create-delivery-stream \
    --delivery-stream-name ${FIREHOSE_DELIVERY_STREAM_NAME} \
    --delivery-stream-type DirectPut \
    --elasticsearch-destination-configuration "$(envsubst_to_str config/cloudformation/kinesis_firehose_data_stream_to_elastic_search_template.json '$ES_ARN $FIREHOSE_ROLE_ARN $FIREHOSE_LOG_GROUP_NAME $FIREHOSE_ROLE_ARN $FIREHOSE_S3_BUCKET_ARN $FIREHOSE_S3_LOG_GROUP_NAME $AWS_KMS_KEY $FIREHOSE_PREPROCESS_LAMBDA_ARN')" 
}

setup_cwl_to_firehose_stream() {

  aws iam create-role \
      --role-name ${CWL_TO_KINESIS_ROLE} \
      --assume-role-policy-document file://`pwd`/config/iam-policy-templates/TrustPolicyForCWL.json \
    2> /dev/null \
    || echo "CWL KINESIS FIREHOSE IAM role already exists."

  aws iam put-role-policy \
      --role-name ${CWL_TO_KINESIS_ROLE} \
      --policy-name Permissions-Policy-For-CWL \
      --policy-document "$(envsubst_to_str config/iam-policy-templates/PermissionsForCWL.json '$CWL_TO_KINESIS_ROLE_ARN')" \
    2> /dev/null \
    || echo "CWL KINESIS FIREHOSE policy already exists."
}


setup_log_exporter() {
  export SERVICE=lambda

  # create export role and policy
  aws iam create-role \
    --role-name ${ELK_EXPORT_ROLE_NAME} \
    --assume-role-policy-document "$(envsubst_to_str config/iam-policy-templates/assume_role.json '$SERVICE')" \
    2> /dev/null \
    || echo "${ELK_EXPORT_ROLE_NAME} IAM role already exists."

  aws iam put-role-policy \
    --role-name ${ELK_EXPORT_ROLE_NAME} \
    --policy-name ExportLogs \
    --policy-document file://`pwd`/config/iam-policy-templates/lambda_elasticsearch_execution.json \
    2> /dev/null \
    || echo "Policy for ${ELK_EXPORT_ROLE_NAME} already exists."

  aws lambda create-function \
    --cli-input-json "$(envsubst_to_str config/iam-policy-templates/cwl-to-elk-exporter-lambda-deployment.json '$ES_ENDPOINT $ELK_EXPORT_ROLE_ARN')" \
    2> /dev/null \
    || echo "Lambda function already exists!"
  aws lambda add-permission \
    --cli-input-json "$(envsubst_to_str config/iam-policy-templates/lambda_permission.json '$ACCOUNT_ID')" \
    2> /dev/null \
    || echo "Permission already exists!"
}


setup_alerts() {
  # TODO: send this to a broader set of users
  aws cloudformation create-stack \
    --stack-name CloudTrail-Monitoring \
    --template-body file://`pwd`/config/cloudformation/CloudWatch_Alarms_for_CloudTrail_API_Activity.json \
    --parameters ParameterKey=LogGroupName,ParameterValue=${CLOUDTRAIL_LOG_GROUP_NAME} ParameterKey=Email,ParameterValue=mweiden@chanzuckerberg.com
}

echo_help() {
    echo
    echo "${0} [system]"
    echo -e "\tsystem ∈ {cloudtrail, elk, log-exporter, gcp-exporter}"
    echo
}

PARAMETERIZED=true

for var in "${USER_DEFINED_VAR_ARRAY[@]}" ; do
  if [[ ${!var} == 'undefined' ]]; then
    echo "${var} is undefined"
    PARAMETERIZED=false
  fi
done

[[ ! PARAMETERIZED ]] && exit 1


##
# switch
#
case "$1" in
  'cloudtrail')
    setup_cloudtrail
    ;;
  'kinesis-firehose-stream')
    setup_kinesis_firehose_stream
    ;;
  'cwl-to-firehose-stream')
    setup_cwl_to_firehose_stream
    ;;
  'elk')
    setup_ELK
    ;;
  'configure-log-exporter')
    setup_log_exporter
    ;;
  'alerts')
    setup_alerts
    ;;
  *)
    echo_help
    exit 1
  ;;
esac
