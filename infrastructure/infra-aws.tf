////
// test fixtures
//

resource "aws_s3_bucket" "test_fixtures" {
  bucket = "logs-test-${var.account_id}"
  tags = "${merge(
    map(
        "Name", "logs",
        "Environment", "default"
    ),
    local.common_tags
  )}"
}

////
// CloudTrail
//

variable "account_id" {}
variable "cloudtrail_log_group_name" {}
variable "cloudtrail_name" {}

resource "aws_s3_bucket" "cloudtrail" {
  bucket = "${var.account_id}-cloudtrail"
  policy = <<POLICY
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AWSCloudTrailAclCheck20150319",
            "Effect": "Allow",
            "Principal": {"Service": "cloudtrail.amazonaws.com"},
            "Action": "s3:GetBucketAcl",
            "Resource": "arn:aws:s3:::${var.account_id}-cloudtrail"
        },
        {
            "Sid": "AWSCloudTrailWrite20150319",
            "Effect": "Allow",
            "Principal": {"Service": "cloudtrail.amazonaws.com"},
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::${var.account_id}-cloudtrail/AWSLogs/${var.account_id}/*",
            "Condition": {"StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}}
        }
    ]
}
POLICY
  tags = "${local.common_tags}"
}

resource "aws_cloudtrail" "audit" {
  name = "${var.cloudtrail_name}"
  s3_bucket_name = "${aws_s3_bucket.cloudtrail.bucket}"
  cloud_watch_logs_role_arn = "${aws_iam_role.cloudtrail.arn}"
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.cloudtrail.arn}"
  enable_log_file_validation = true
  is_multi_region_trail = true
  depends_on = [
    "aws_s3_bucket.cloudtrail"
  ]
  tags = "${local.common_tags}"
}

resource "aws_iam_role" "cloudtrail" {
  name = "logging-aws-cloudtrail"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudtrail.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
  tags = "${local.common_tags}"
}

resource "aws_iam_role_policy" "cloudtrail" {
  name = "cloudtrail-policy"
  role = "logging-aws-cloudtrail"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {

      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream"
      ],
      "Resource": [
        "arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:${aws_cloudwatch_log_group.cloudtrail.name}:log-stream:${var.account_id}_CloudTrail_${var.aws_region}*"
      ]

    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:${aws_cloudwatch_log_group.cloudtrail.name}:log-stream:${var.account_id}_CloudTrail_${var.aws_region}*"
      ]
    }
  ]
}
EOF
}

resource "aws_cloudwatch_log_group" "cloudtrail" {
  name = "${var.cloudtrail_log_group_name}"
  retention_in_days = "731"
  tags = "${local.common_tags}"
}


////
// ElasticSearch
//

variable "es_domain_name" {}
variable "travis_user" {}

variable "es_principal_arns" {
  type = "list"
}

data "aws_secretsmanager_secret" "user_groups" {
  name = "hca-id-groups.json"
}

data "aws_secretsmanager_secret_version" "user_groups" {
  secret_id = "${data.aws_secretsmanager_secret.user_groups.id}"
}

locals {
  user_groups = "${jsondecode(data.aws_secretsmanager_secret_version.user_groups.secret_string)}"
  es_principal_emails = "${
    concat(
        lookup(local.user_groups, "dcp_admin"),
        lookup(local.user_groups, "dcp_developer")
    )
  }"
}

resource "aws_elasticsearch_domain" "es" {
  domain_name = "${var.es_domain_name}"
  elasticsearch_version = "5.5"

  cluster_config {
    instance_type = "m5.xlarge.elasticsearch"
    instance_count = 3
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp2"
    volume_size = 512
  }

  access_policies = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    ${join(
        ", ",
        formatlist(
           "{\"Effect\": \"Allow\",\"Principal\": {\"AWS\": \"arn:aws:sts::%s:assumed-role/elk-oidc-proxy/%s\"}, \"Action\": \"es:*\", \"Resource\": \"arn:aws:es:%s:%s:domain/hca-logs/*\" }",
           var.account_id,
           local.es_principal_emails,
           var.aws_region,
           var.account_id
        )
    )},
    ${join(
        ", ",
        formatlist(
           "{\"Effect\": \"Allow\", \"Principal\": { \"AWS\": \"%s\" }, \"Action\": \"es:*\", \"Resource\": \"arn:aws:es:%s:%s:domain/hca-logs/*\" }",
           var.es_principal_arns,
           var.aws_region,
           var.account_id
        )
    )}
  ]
}
EOF
  tags = "${local.common_tags}"
}


////
// Alerts
//

resource "aws_cloudformation_stack" "alerts" {
  name = "CloudTrail-Monitoring"
  template_body = "${file("./CloudWatch_Alarms_for_CloudTrail_API_Activity.json")}"
  parameters = {
    LogGroupName = "${aws_cloudwatch_log_group.cloudtrail.name}"
  }
  tags = "${local.common_tags}"
}


////
// GCP to CloudWatch Logs exporter
//

variable "deployment_stage" {}

resource "aws_iam_role" "gcp_to_cwl" {
  name = "gcp-to-cwl-exporter-${var.deployment_stage}"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
  tags = "${local.common_tags}"
}

resource "aws_iam_role_policy" "gcp_to_cwl" {
  name = "gcp-to-cwl-exporter-${var.deployment_stage}"
  role = "gcp-to-cwl-exporter-${var.deployment_stage}"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "*"
        }
    ]
}
EOF
}

////
// Firehose to ES
//

resource "aws_iam_role" "kinesis-firehose-es" {
  name = "kinesis-firehose-es"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "firehose.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
  tags = "${local.common_tags}"
}

resource "aws_iam_role_policy" "kinesis-firehose-es" {
  name = "kinesis-firehose-es"
  role = "kinesis-firehose-es"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::kinesis-firehose-logs-${var.account_id}/*"
        }
    ]
}
EOF
}

////
// Firehose S3 Bucket and Log Group
//

resource "aws_s3_bucket" "kinesis-firehose-logs" {
  bucket = "kinesis-firehose-logs-${var.account_id}"
  acl = "private"

  tags = "${merge(
    map(
        "Name", "logs",
        "Environment", "default"
    ),
    local.common_tags
  )}"
}

output "kinesis_bucket" {
  value = "${aws_s3_bucket.kinesis-firehose-logs.arn}"
}

resource "aws_cloudwatch_log_group" "firehose_errors" {
  name = "/aws/kinesisfirehose/Kinesis-Firehose-ES"
  retention_in_days = 1827
  tags = "${local.common_tags}"
}

resource "aws_cloudwatch_log_stream" "firehose_s3_delivery_errors" {
  name = "S3Delivery"
  log_group_name = "/aws/kinesisfirehose/Kinesis-Firehose-ES"
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = "${aws_s3_bucket.kinesis-firehose-logs.id}"

  lambda_function {
    lambda_function_arn = "arn:aws:lambda:us-east-1:${var.account_id}:function:Firehose-CWL-Processor"
    events = [
      "s3:ObjectCreated:*"]
  }
}

////
// Firehose S3 Delivery Stream
//

resource "aws_kinesis_firehose_delivery_stream" "Kinesis-Firehose-ELK" {
  name = "Kinesis-Firehose-ELK"
  destination = "s3"
  s3_configuration {
    role_arn = "${aws_iam_role.kinesis-firehose-es.arn}"
    bucket_arn = "${aws_s3_bucket.kinesis-firehose-logs.arn}"
    buffer_size = 20
    buffer_interval = 60
    prefix = "firehose"
    cloudwatch_logging_options {
      enabled = true
      log_group_name = "/aws/kinesisfirehose/Kinesis-Firehose-ES"
      log_stream_name = "S3Delivery"
    }
  }
  tags = "${local.common_tags}"
}

////
// CWL to firehose
//

resource "aws_iam_role" "cwl-firehose" {
  name = "cwl-firehose"
  assume_role_policy = <<EOF
{
  "Version": "2008-10-17",
  "Statement": {
    "Effect": "Allow",
    "Principal": {
      "Service": [
        "logs.${var.aws_region}.amazonaws.com",
        "lambda.amazonaws.com"
      ]
    },
    "Action": "sts:AssumeRole"
  }
}
EOF
  tags = "${local.common_tags}"
}

resource "aws_iam_role_policy" "cwl-firehose" {
  name = "cwl-firehose"
  role = "cwl-firehose"
  policy = <<EOF
{
    "Statement":[
      {
        "Effect":"Allow",
        "Action":["firehose:*"],
        "Resource":["${aws_kinesis_firehose_delivery_stream.Kinesis-Firehose-ELK.arn}"]
      },
      {
        "Effect":"Allow",
        "Action":["iam:PassRole"],
        "Resource":[
          "${aws_iam_role.cwl-firehose.arn}"
        ]
      }
    ]
}
EOF
}
