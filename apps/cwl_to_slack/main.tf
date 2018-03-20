variable "region" {
  default = "us-east-1"
}

provider "aws" {
  region = "${var.region}"
  profile = "hca"
}

terraform {
  backend "s3" {
    key = "logs/cwl-to-slack-notifier.tfstate"
    region = "us-east-1"
  }
}


variable "kms_key_arn" {}
variable "account_id" {}
variable "target_zip_path" {}

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

resource "aws_iam_role_policy" "slack_notifier_kms" {
  name = "${aws_iam_role.slack_notifier.name}-kms"
  role = "${aws_iam_role.slack_notifier.name}"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": "*"
        }
    ]
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
            "Resource": "arn:aws:logs:${var.region}:${var.account_id}:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:${var.region}:${var.account_id}:log-group:/aws/lambda/${aws_lambda_function.slack_notifier.function_name}:*"
            ]
        }
    ]
}
EOF
}

resource "aws_lambda_function" "slack_notifier" {
  function_name = "cloudwatch-slack-notifications"
  filename = "${var.target_zip_path}"
  description = "An Amazon SNS trigger that sends CloudWatch alarm notifications to Slack."
  runtime = "nodejs6.10"
  handler = "index.handler"
  memory_size = 128
  role = "${aws_iam_role.slack_notifier.arn}"
  environment {
    variables {
      slackChannel = "dcp-ops-alerts"
      kmsEncryptedHookUrl = "AQICAHjW6Fl+muQzFxxa9kzPYcoDbRQsv97HjGgv3NJ9273zjgH8N/FoUSlu7ZIBEDVslJSkAAAApzCBpAYJKoZIhvcNAQcGoIGWMIGTAgEAMIGNBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDMFgvV6b0LV7ANf3sgIBEIBggKlGKXqbOGmY07NGLZZ2ouSD5broJ2JsFC0ETwYnzCzXp+1/y4eNAc8yeGGxlLDvn63EILBLl2EJdq3jf8qsdIwR2mdmSfXjkMzdTPLGih29DseVgfcCuHWoNGPffb8u"
      region = "${var.region}"
    }
  }
  kms_key_arn = "${var.kms_key_arn}"
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
}

resource "aws_sns_topic_subscription" "alarms" {
  topic_arn = "${aws_sns_topic.alarms.arn}"
  protocol = "lambda"
  endpoint = "${aws_lambda_function.slack_notifier.arn}"
}
