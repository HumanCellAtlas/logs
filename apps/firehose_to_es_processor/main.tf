data "aws_caller_identity" "current" {}
variable "aws_profile" {}
variable "aws_region" {}
variable "logs_lambda_bucket" {}
variable "path_to_zip_file" {}
variable "account_id" {}


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
    key = "logs/firehose-to-es-processor.tfstate"
  }
}

////
//  Firehose To Es Processor
//


resource "aws_iam_role" "firehose_processor" {
  name               = "firehose-cwl-log-processor"
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

resource "aws_iam_role_policy" "firehose_processor" {
  name   = "firehose-cwl-log-processor"
  role   = "firehose-cwl-log-processor"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "es:*",
            "Resource": "arn:aws:es:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::kinesis-firehose-logs-${var.account_id}/*"
        },
        {
            "Effect": "Allow",
            "Action": "cloudwatch:PutMetricData",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:${var.aws_region}:${var.account_id}:secret:logs/*"
        }
    ]
}
EOF
  depends_on = [
    "aws_iam_role.firehose_processor"
  ]
}

resource "aws_lambda_function" "firehose_cwl_processor" {
  description = "Processes CloudWatch Logs from Firehose"
  function_name = "Firehose-CWL-Processor"
  s3_bucket = "${var.logs_lambda_bucket}"
  s3_key = "${var.path_to_zip_file}"
  role = "${aws_iam_role.firehose_processor.arn}"
  handler = "app.handler"
  runtime = "python3.6"
  memory_size = 2048
  timeout = 600
  reserved_concurrent_executions = 5
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = "arn:aws:lambda:${var.aws_region}:${var.account_id}:function:Firehose-CWL-Processor"
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::kinesis-firehose-logs-${var.account_id}"
  depends_on = ["aws_lambda_function.firehose_cwl_processor"]
}


resource "aws_cloudwatch_log_group" "firehose_cwl_processor" {
  name = "/aws/lambda/Firehose-CWL-Processor"
  retention_in_days = 1827

}
