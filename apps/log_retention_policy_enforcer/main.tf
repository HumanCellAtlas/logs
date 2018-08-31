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
    key = "logs/log_retention_policy_enforcer.tfstate"
  }
}

////
//  Health check app
//

resource "aws_iam_role" "log_retenion_policy_enforcer" {
  name = "log-retention-policy-enforcer"
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

resource "aws_iam_role_policy" "log_retenion_policy_enforcer" {
  name   = "log-retention-policy-enforcer"
  role   = "${aws_iam_role.log_retenion_policy_enforcer.name}"
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
            "Resource": [
                "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/log-retention-policy-enforcer:*:*",
                "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/log-retention-policy-enforcer"
            ]
        },
        {
          "Effect": "Allow",
          "Action": [
            "logs:DescribeLogGroups",
            "logs:PutRetentionPolicy"
          ],
          "Resource": "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:*"
        },
        {
            "Effect": "Allow",
            "Action": "es:*",
            "Resource": "arn:aws:es:*:*:*"
        }
    ]
}
EOF
  depends_on = [
    "aws_iam_role.log_retenion_policy_enforcer"
  ]
}


resource "aws_lambda_function" "log_retention_policy_enforcer" {
  function_name = "log-retention-policy-enforcer"
  description = "Enforces log retention policies"
  s3_bucket = "${var.logs_lambda_bucket}"
  s3_key = "${var.path_to_zip_file}"
  role = "${aws_iam_role.log_retenion_policy_enforcer.arn}"
  handler = "app.handler"
  runtime = "python3.6"
  memory_size = 256
  timeout = 120
  environment {
    variables = {
      LOG_RETENTION_TTL_FILE = "./log_retention_ttl"
    }
  }
}


////
//  Timer
//

resource "aws_cloudwatch_event_rule" "log_retention_policy_enforcer" {
  name = "log-retention-policy-enforcer"
  description = "Trigger the es-idx-manager app"
  schedule_expression = "rate(2 days)"
}

resource "aws_lambda_permission" "dss" {
  statement_id = "AllowExecutionFromCloudWatch"
  principal = "events.amazonaws.com"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.log_retention_policy_enforcer.function_name}"
  source_arn = "${aws_cloudwatch_event_rule.log_retention_policy_enforcer.arn}"
  depends_on = [
    "aws_lambda_function.log_retention_policy_enforcer"
  ]
}

resource "aws_cloudwatch_event_target" "dss" {
  rule      = "${aws_cloudwatch_event_rule.log_retention_policy_enforcer.name}"
  target_id = "invoke-log-retention-policy-enforcer"
  arn       = "${aws_lambda_function.log_retention_policy_enforcer.arn}"
}
