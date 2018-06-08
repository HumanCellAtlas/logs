variable "aws_profile" {}
data "aws_caller_identity" "current" {}

variable "aws_region" {
  default = "us-east-1"
}

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
    key = "logs/gcp_to_cwl.tfstate"
  }
}

////
//  Health check app
//

resource "aws_iam_role" "gcp_to_cwl" {
  name = "gcp-to-cwl"
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
  name   = "gcp-to-cwl"
  role   = "${aws_iam_role.gcp_to_cwl.name}"
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
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:logs/*"
        }
    ]
}
EOF
  depends_on = [
    "aws_iam_role.gcp_to_cwl"
  ]
}

data "archive_file" "lambda_zip" {
  type = "zip"
  source_dir = "./target"
  output_path = "./lambda.zip"
}

resource "aws_lambda_function" "gcp_to_cwl" {
  function_name = "gcp-to-cwl-exporter"
  description = "Exports logs from GCP to AWS CloudWatch"
  filename = "${data.archive_file.lambda_zip.output_path}"
  role = "${aws_iam_role.gcp_to_cwl.arn}"
  handler = "app.handler"
  runtime = "python3.6"
  memory_size = 512
  timeout = 120
  source_code_hash = "${base64sha256(file("${data.archive_file.lambda_zip.output_path}"))}"
  environment {
    variables {
      GOOGLE_APPLICATION_CREDENTIALS = "./gcp-credentials.json"
    }
  }
  depends_on = [
    "data.archive_file.lambda_zip"
  ]
}


////
//  Timer
//

resource "aws_cloudwatch_event_rule" "gcp_to_cwl" {
  name = "log-retention-policy-enforcer"
  description = "Triggers the export of logs from GCP to AWS CloudWatch"
  schedule_expression = "rate(2 minutes)"
}

resource "aws_lambda_permission" "dss" {
  statement_id = "AllowExecutionFromCloudWatch"
  principal = "events.amazonaws.com"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.gcp_to_cwl.function_name}"
  source_arn = "${aws_cloudwatch_event_rule.gcp_to_cwl.arn}"
  depends_on = [
    "aws_lambda_function.gcp_to_cwl"
  ]
}

resource "aws_cloudwatch_event_target" "dss" {
  rule      = "${aws_cloudwatch_event_rule.gcp_to_cwl.name}"
  target_id = "invoke-gcp-to-cwl-exporter-enforcer"
  arn       = "${aws_lambda_function.gcp_to_cwl.arn}"
}
