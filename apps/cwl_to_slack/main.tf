variable "aws_profile" {}
variable "app_name" {
  default = "cloudwatch-slack-notifier"
}

data "aws_caller_identity" "current" {}

variable "aws_region" {
  default = "us-east-1"
}

provider "aws" {
  region = "${var.aws_region}"
  profile = "${var.aws_profile}"
}

terraform {
  backend "s3" {
    key = "logs/cwl-to-slack-notifier.tfstate"
  }
}


resource "aws_iam_role" "slack_notifier" {
  name = "CloudWatchSlackNotifier"
  path = "/service-role/"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Allow",
    "Principal": { "Service": "lambda.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }
}
EOF
}

resource "aws_iam_role_policy" "slack_notifier_logs" {
  name = "${aws_iam_role.slack_notifier.name}-logs"
  role = "${aws_iam_role.slack_notifier.name}"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.app_name}:*"
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
}

data "archive_file" "lambda_zip" {
  type = "zip"
  source_dir = "./target"
  output_path = "./lambda.zip"
}

resource "aws_lambda_function" "slack_notifier" {
  function_name = "${var.app_name}"
  filename = "${data.archive_file.lambda_zip.output_path}"
  description = "An Amazon SNS trigger that sends CloudWatch alarm notifications to Slack."
  runtime = "nodejs6.10"
  handler = "index.handler"
  memory_size = 128
  role = "${aws_iam_role.slack_notifier.arn}"
  source_code_hash = "${base64sha256(file("${data.archive_file.lambda_zip.output_path}"))}"
  depends_on = [
    "aws_iam_role.slack_notifier",
    "aws_sns_topic.alarms"
  ]
}

resource "aws_sns_topic" "alarms" {
  name = "cloudwatch-alarms"
}

resource "aws_lambda_permission" "alarms" {
  statement_id  = "AllowExecutionFromSNS"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.slack_notifier.function_name}"
  principal = "sns.amazonaws.com"
  source_arn = "${aws_sns_topic.alarms.arn}"
  depends_on = [
    "aws_sns_topic.alarms",
    "aws_lambda_function.slack_notifier"
  ]
}

resource "aws_sns_topic_subscription" "alarms" {
  topic_arn = "${aws_sns_topic.alarms.arn}"
  protocol = "lambda"
  endpoint = "${aws_lambda_function.slack_notifier.arn}"
  depends_on = [
    "aws_sns_topic.alarms",
    "aws_lambda_function.slack_notifier"
  ]
}