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
    --access-policies "$(envsubst_to_str config/iam-policy-templates/es-access.json '$ES_USER_ARRAY $IP_ADDRESS_ARRAY $REGION $ACCOUNT_ID')")

  status_report "ELK Stack" $? "$ES_DOMAIN_RESULT"
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
    || echo "Policy for ${ELK_EXPORT_ROLE_NAME} already exists."

  # make the application and deploy it
  rm -rf $SOURCE_DIR/target
  mkdir $SOURCE_DIR/target
  ZIP_FILE=LogsToElasticsearch_App.zip
  TARGET=$SOURCE_DIR/target/$ZIP_FILE

  cd exporters/cwl_to_elk/ && zip -r $TARGET ./{*.js,node_modules,package.json,package-lock.json} && cd -

  aws s3 rm s3://${CODE_DEPLOYMENT_BUCKET}/${ZIP_FILE}

  aws s3 cp \
    $TARGET \
    s3://${CODE_DEPLOYMENT_BUCKET}/$ZIP_FILE

  aws lambda create-function \
    --cli-input-json "$(envsubst_to_str exporters/cwl_to_elk/lambda-deployment.json '$ES_ENDPOINT $ELK_EXPORT_ROLE_ARN')" \
    || echo "Lambda function already exists!"

  aws lambda add-permission \
    --cli-input-json "$(envsubst_to_str config/iam-policy-templates/lambda_permission.json '$ACCOUNT_ID')" \
    || echo "Permission already exists!"
}


setup_gcp_exporter() {
  export SERVICE=lambda

  # create export role and policy
  aws iam create-role \
    --role-name ${GCP_EXPORT_ROLE_NAME} \
    --assume-role-policy-document "$(envsubst_to_str config/iam-policy-templates/assume_role.json '$SERVICE')" \
    2> /dev/null \
    || echo "${GCP_EXPORT_ROLE_NAME} IAM role already exists."

  aws lambda delete-function --function-name function:gcp-to-cwl-exporter-dev \
    || echo "Function gcp-to-cwl-exporter-dev does not exist."
  aws lambda delete-function --function-name function:gcp-to-cwl-exporter-staging \
    || echo "Function gcp-to-cwl-exporter-staging does not exist."

  DEPLOYMENT_STAGE=staging make -C exporters/gcp_to_cwl/ deploy
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
  'elk')
    setup_ELK
    ;;
  'log-exporter')
    setup_log_exporter
    ;;
  'gcp-exporter')
    setup_gcp_exporter
    ;;
  *)
    echo_help
    exit 1
  ;;
esac
