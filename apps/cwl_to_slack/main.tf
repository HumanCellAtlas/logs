variable "aws_profile" {}
variable "slack_webhook_url" {}
variable "slack_alert_channel" {}

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
            "Resource": "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
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

resource "aws_kms_key" "cw_to_slack" {
  description = "cw-to-slack"
  is_enabled = true
  policy = <<POLICY
{
  "Version" : "2012-10-17",
  "Id" : "key-consolepolicy-3",
  "Statement" : [ {
    "Sid" : "Enable IAM User Permissions",
    "Effect" : "Allow",
    "Principal" : {
      "AWS" : "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
    },
    "Action" : "kms:*",
    "Resource" : "*"
  }, {
    "Sid" : "Allow use of the key",
    "Effect" : "Allow",
    "Principal" : {
      "AWS" : "${aws_iam_role.slack_notifier.arn}"
    },
    "Action" : [ "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:DescribeKey" ],
    "Resource" : "*"
  }, {
    "Sid" : "Allow attachment of persistent resources",
    "Effect" : "Allow",
    "Principal" : {
      "AWS" : "${aws_iam_role.slack_notifier.arn}"
    },
    "Action" : [ "kms:CreateGrant", "kms:ListGrants", "kms:RevokeGrant" ],
    "Resource" : "*",
    "Condition" : {
      "Bool" : {
        "kms:GrantIsForAWSResource" : "true"
      }
    }
  } ]
}
POLICY
}

data "aws_kms_ciphertext" "slack_webhook_url" {
  key_id = "${aws_kms_key.cw_to_slack.key_id}"
  plaintext = "${var.slack_webhook_url}"
  depends_on = [
    "aws_kms_key.cw_to_slack"
  ]
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
      slackChannel = "${var.slack_alert_channel}"
      kmsEncryptedHookUrl = "${data.aws_kms_ciphertext.slack_webhook_url.ciphertext_blob}"
      region = "${var.aws_region}"
    }
  }
  kms_key_arn = "${aws_kms_key.cw_to_slack.arn}"
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
