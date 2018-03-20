variable "aws_region" {
  default = "us-east-1"
}

provider "aws" {
    region = "${var.aws_region}"
}

////
// general setup
//

// the bucket must be configured with the -backend-config flag on `terraform init`

terraform {
  backend "s3" {
    key = "logs/cwl-firehose-subscriber.tfstate"
    region = "us-east-1"
  }
}

////
//  CWL Firehose subscriber
//

variable "target_zip_path" {}
variable "account_id" {}
variable "blacklisted_log_groups" {}

resource "aws_iam_role" "cwl_firehose_subscriber" {
  name               = "cwl_firehose_subscriber-staging"
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

resource "aws_iam_role_policy" "cwl_firehose_subscriber" {
  name   = "cwl_firehose_subscriber-staging"
  role   = "cwl_firehose_subscriber-staging"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:PutSubscriptionFilter",
                "logs:CreateLogGroup"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
          "Effect":"Allow",
          "Action":["iam:PassRole"],
          "Resource":[
            "arn:aws:iam::${var.account_id}:role/cwl-firehose-staging"
          ]
        }
    ]
}
EOF

depends_on = ["aws_iam_role.cwl_firehose_subscriber"]
}

resource "aws_lambda_function" "cwl_firehose_subscriber" {
    filename = "${var.target_zip_path}"
    function_name = "cwl_firehose_subscriber"
    role = "${aws_iam_role.cwl_firehose_subscriber.arn}"
    handler = "app.handler"
    runtime = "python3.6"
    timeout = 10
    source_code_hash = "${base64sha256(file("${var.target_zip_path}"))}"

    environment {
      variables = {
        BLACKLISTED_LOG_GROUPS = "${var.blacklisted_log_groups}"
      }
    }
}

resource "aws_cloudwatch_log_group" "cwl_firehose_subscriber" {
  name = "/aws/lambda/cwl_firehose_subscriber"
}

resource "aws_cloudwatch_event_rule" "create_log_group" {
  name        = "capture_create_log_group"
  description = "Capture each Create Log Group"

  event_pattern = <<PATTERN
{
  "source": [
    "aws.logs"
  ],
  "detail-type": [
    "AWS API Call via CloudTrail"
  ],
  "detail": {
    "eventSource": [
      "logs.amazonaws.com"
    ],
    "eventName": [
      "CreateLogGroup"
    ]
  }
}
PATTERN
depends_on = [
    "aws_lambda_function.cwl_firehose_subscriber"
  ]
}

resource "aws_cloudwatch_event_target" "cwl_firehose_subscriber_lambda" {
  rule      = "${aws_cloudwatch_event_rule.create_log_group.name}"
  target_id = "cwl_firehose_subscriber"
  arn       = "${aws_lambda_function.cwl_firehose_subscriber.arn}"
}

resource "aws_lambda_permission" "cwl_firehose_subscriber" {
  statement_id = "AllowExecutionFromCloudWatch"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.cwl_firehose_subscriber.function_name}"
  principal = "events.amazonaws.com"
  source_arn = "${aws_cloudwatch_event_rule.create_log_group.arn}"
}
