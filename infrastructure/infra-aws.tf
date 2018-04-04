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
}

resource "aws_cloudtrail" "audit" {
  name                       = "${var.cloudtrail_name}"
  s3_bucket_name             = "${aws_s3_bucket.cloudtrail.bucket}"
  cloud_watch_logs_role_arn  = "${aws_iam_role.cloudtrail.arn}"
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.cloudtrail.arn}"
  enable_log_file_validation = true
  is_multi_region_trail      = true
  depends_on = [
    "aws_s3_bucket.cloudtrail"
  ]
}

resource "aws_iam_role" "cloudtrail" {
  name               = "logging-aws-cloudtrail"
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
}

resource "aws_iam_role_policy" "cloudtrail" {
  name   = "cloudtrail-policy"
  role   = "logging-aws-cloudtrail"
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
}


////
// ElasticSearch
//

variable "es_domain_name" {}
variable "travis_user" {}
variable "es_email_principals" {
  type = "list"
}

resource "aws_elasticsearch_domain" "es" {
  domain_name = "${var.es_domain_name}"
  elasticsearch_version = "5.5"

  cluster_config {
    instance_type = "m3.xlarge.elasticsearch"
    instance_count = 2
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
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          ${join(", ", sort(formatlist("\"arn:aws:sts::%s:assumed-role/elk-oidc-proxy/%s\"", var.account_id, var.es_email_principals)))},
          "arn:aws:iam::${var.account_id}:user/${var.travis_user}"
        ]
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:*:*:*"
    }
  ]
}
EOF
}


////
// Alerts
//

resource "aws_cloudformation_stack" "alerts" {
  name = "CloudTrail-Monitoring"
  template_body = "${file("./CloudWatch_Alarms_for_CloudTrail_API_Activity.json")}"
  parameters {
    LogGroupName = "${aws_cloudwatch_log_group.cloudtrail.name}"
  }
}


////
// GCP to CloudWatch Logs exporter
//

resource "aws_iam_role" "gcp_to_cwl" {
  name               = "gcp-to-cwl-exporter"
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
}

resource "aws_iam_role_policy" "gcp_to_cwl" {
  name   = "gcp-to-cwl-exporter"
  role   = "gcp-to-cwl-exporter"
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
  name               = "kinesis-firehose-es"
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
}

resource "aws_iam_role_policy" "kinesis-firehose-es" {
  name   = "kinesis-firehose-es"
  role   = "kinesis-firehose-es"
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
            "Action": "es:*",
            "Resource": "arn:aws:es:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::*"
        },
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction",
                "lambda:GetFunctionConfiguration"
            ],
            "Resource": "arn:aws:lambda:${var.aws_region}:${var.account_id}:function:Firehose-CWL-Processor"
        }
    ]
}
EOF
}

////
// Firehose S3 Bucket and Log Group
//

resource "aws_s3_bucket" "kinesis-es-firehose-failures" {
  bucket = "kinesis-es-firehose-failures-${var.account_id}"
  acl    = "private"

  tags {
    Name        = "kinesis-es-firehose-failures"
    Environment = "default"
  }
}

resource "aws_cloudwatch_log_group" "firehose_errors" {
  name = "/aws/kinesisfirehose/Kinesis-Firehose-ES"
}


resource "aws_cloudwatch_log_stream" "firehose_es_delivery_errors" {
  name = "ElasticsearchDelivery"
  log_group_name = "/aws/kinesisfirehose/Kinesis-Firehose-ES"
}

resource "aws_cloudwatch_log_stream" "firehose_s3_delivery_errors" {
  name = "S3Delivery"
  log_group_name = "/aws/kinesisfirehose/Kinesis-Firehose-ES"
}


////
// Firehose ES Delivery Stream
//

resource "aws_kinesis_firehose_delivery_stream" "Kinesis-Firehose-ELK" {
  name        = "Kinesis-Firehose-ELK"
  destination = "elasticsearch"
  s3_configuration {
    role_arn           = "${aws_iam_role.kinesis-firehose-es.arn}"
    bucket_arn         = "${aws_s3_bucket.kinesis-es-firehose-failures.arn}"
    buffer_size        = 1
    buffer_interval    = 60
    compression_format = "GZIP"
    prefix = "firehose"
    cloudwatch_logging_options {
      enabled = true
      log_group_name = "/aws/kinesisfirehose/Kinesis-Firehose-ES"
      log_stream_name = "S3Delivery"
    }
  }
  elasticsearch_configuration {
    domain_arn = "${aws_elasticsearch_domain.es.arn}"
    role_arn   = "${aws_iam_role.kinesis-firehose-es.arn}"
    index_name = "cwl"
    type_name  = "fromFirehose"
    buffering_interval = 60
    buffering_size = 1
    retry_duration = 300
    index_rotation_period = "OneDay"
    s3_backup_mode = "FailedDocumentsOnly"
    cloudwatch_logging_options {
      enabled = true
      log_group_name = "/aws/kinesisfirehose/Kinesis-Firehose-ES"
      log_stream_name = "ElasticsearchDelivery"
    }
  }
}

////
// CWL to firehose
//

resource "aws_iam_role" "cwl-firehose" {
  name               = "cwl-firehose"
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
}

resource "aws_iam_role_policy" "cwl-firehose" {
  name   = "cwl-firehose"
  role   = "cwl-firehose"
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
