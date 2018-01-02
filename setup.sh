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
    --assume-role-policy-document file://`pwd`/policies/assume_role.json \
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
    --policy-document "$(envsubst_to_str policies/role.json '$REGION $LOG_GROUP_NAME $ACCOUNT_ID')"

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
  read -p "Enter (space separated) admin ElasticSearch AWS users: " users
  user_arns=()
  for user in $users; do
    user_arns+=("arn:aws:iam::${ACCOUNT_ID}:user/${user}")
  done
  export ES_USER_ARRAY="\"$(echo ${user_arns[@]} | sed 's/ /", "/g')\""
  export IP_ADDRESS_ARRAY="\"$(curl http://checkip.amazonaws.com/)\""

  # create domain
  ES_DOMAIN_RESULT=$(aws es create-elasticsearch-domain \
    --domain-name ${ES_DOMAIN_NAME} \
    --elasticsearch-version 6.1 \
    --elasticsearch-cluster-config InstanceType=t2.small.elasticsearch,InstanceCount=1 \
    --ebs-options EBSEnabled=true,VolumeType=standard,VolumeSize=10 \
    --access-policies "$(envsubst_to_str policies/es-access.json '$ES_USER_ARRAY $IP_ADDRESS_ARRAY $REGION $ACCOUNT_ID')")

  status_report "ELK Stack" $? "$ES_DOMAIN_RESULT"
}


setup_log_exporter() {
  export SERVICE=lambda

  # create export role and policy
  aws iam create-role \
    --role-name ${EXPORT_ROLE_NAME} \
    --assume-role-policy-document "$(envsubst_to_str policies/assume_role.json '$SERVICE')" \
    2> /dev/null \
    || echo "${EXPORT_ROLE_NAME} IAM role already exists."

  aws iam put-role-policy \
    --role-name ${EXPORT_ROLE_NAME} \
    --policy-name ExportLogs \
    --policy-document file://`pwd`/policies/lambda_elasticsearch_execution.json \
    || echo "Policy for ${EXPORT_ROLE_NAME} already exists."

  # make the application and deploy it
  rm -rf target
  mkdir target

  cp exporters/cwl_to_elk/index.js target/
  cd target && npm install zlib https crypto && cd ..
  cd target && zip -r ../LogsToElasticsearch_App.zip ./* && cd ..

  aws s3 rm s3://${CODE_DEPLOYMENT_BUCKET}/LogsToElasticsearch_App.zip

  aws s3 cp \
    LogsToElasticsearch_App.zip \
    s3://${CODE_DEPLOYMENT_BUCKET}/LogsToElasticsearch_App.zip

  aws lambda create-function \
    --cli-input-json "$(envsubst_to_str exporters/cwl_to_elk/lambda-deployment.json '$ES_ENDPOINT $EXPORT_ROLE_ARN')" \
    || echo "Lambda function already exists!"

  aws lambda add-permission \
    --cli-input-json "$(envsubst_to_str policies/lambda_permission.json '$ACCOUNT_ID')" \
    || echo "Permission already exists!"
}

echo_help() {
    echo
    echo "${0} [system]"
    echo -e "\tsystem ∈ {cloudtrail, elk, log-exporter}"
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
  'elk')
    setup_ELK
    ;;
  'log-exporter')
    setup_log_exporter
    ;;
  *)
    echo_help
    exit 1
  ;;
esac
