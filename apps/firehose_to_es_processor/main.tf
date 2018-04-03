variable "aws_profile" {}

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
    key = "logs/firehose-to-es-processor.tfstate"
  }
}

////
//  Firehose To Es Processor
//

variable "target_zip_path" {}
variable "account_id" {}
variable "airbrake_blacklisted_log_group_names" {}
variable "airbrake_whitelisted_log_message_terms" {}
variable "airbrake_flag" {}
variable "airbrake_api_key" {}
variable "airbrake_project_id" {}
variable "airbrake_environment" {}

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
            "Action": "firehose:*",
            "Resource": "arn:aws:firehose:*:*:*"
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
    filename = "${var.target_zip_path}"
    function_name = "Firehose-CWL-Processor"
    role = "${aws_iam_role.firehose_processor.arn}"
    handler = "app.handler"
    runtime = "python3.6"
    memory_size = 512
    timeout = 120
    source_code_hash = "${base64sha256(file("${var.target_zip_path}"))}"

    environment {
      variables = {
        AIRBRAKE_BLACKLISTED_LOG_GROUP_NAMES="${var.airbrake_blacklisted_log_group_names}"
        AIRBRAKE_WHITELISTED_LOG_MESSAGE_TERMS="${var.airbrake_whitelisted_log_message_terms}"
        AIRBRAKE_FLAG="${var.airbrake_flag}"
        AIRBRAKE_API_KEY="${var.airbrake_api_key}"
        AIRBRAKE_PROJECT_ID="${var.airbrake_project_id}"
        AIRBRAKE_ENVIRONMENT="${var.airbrake_environment}"
      }
    }

}

resource "aws_cloudwatch_log_group" "firehose_cwl_processor" {
  name = "/aws/lambda/Firehose-CWL-Processor"
}

data "external" "processing_configuration" {
  program = ["python", "./setup_firehose_processing_config.py"]

  query = {
    # arbitrary map from strings to strings, passed
    # to the external program as the data query.
    delivery_stream_name = "Kinesis-Firehose-ELK"
    lambda_name = "Firehose-CWL-Processor"
  }
  depends_on = [
    "aws_lambda_function.firehose_cwl_processor"
  ]
}
