data "aws_caller_identity" "current" {}
variable "aws_profile" {}
variable "aws_region" {}
variable "logs_lambda_bucket" {}
variable "path_to_zip_file" {}

provider "aws" {
  region = "${var.aws_region}"
  profile = "${var.aws_profile}"
}

////
// general setup
//

// the bucket must be configured with the -backend-config flag on `terraform init`

terraform {
  backend "s3" {
    key = "logs/cwl-firehose-subscriber.tfstate"
  }
}

////
//  CWL Firehose subscriber
//

variable "account_id" {}

resource "aws_iam_role" "cwl_firehose_subscriber" {
  name               = "cwl_firehose_subscriber"
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
  name   = "cwl_firehose_subscriber"
  role   = "cwl_firehose_subscriber"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:PutSubscriptionFilter"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:CreateLogGroup"
            ],
            "Resource": [
                "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${aws_lambda_function.cwl_firehose_subscriber.function_name}:*:*",
                "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${aws_lambda_function.cwl_firehose_subscriber.function_name}"
            ]
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
            "arn:aws:iam::${var.account_id}:role/cwl-firehose"
          ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:logs/*"
        }
    ]
}
EOF

depends_on = ["aws_iam_role.cwl_firehose_subscriber"]
}

resource "aws_lambda_function" "cwl_firehose_subscriber" {
  function_name = "cwl_firehose_subscriber"
  s3_bucket = "${var.logs_lambda_bucket}"
  s3_key = "${var.path_to_zip_file}"
  role = "${aws_iam_role.cwl_firehose_subscriber.arn}"
  handler = "app.handler"
  runtime = "python3.6"
  timeout = 10
  depends_on = [
    "aws_iam_role.cwl_firehose_subscriber"
  ]
}

resource "aws_cloudwatch_log_group" "cwl_firehose_subscriber" {
  name = "/aws/lambda/cwl_firehose_subscriber"
  retention_in_days = 1827
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
