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
    key = "logs/firehose-to-es-processor.tfstate"
  }
}

////
//  Firehose To Es Processor
//

variable "target_zip_path" {}
variable "account_id" {}

resource "aws_iam_role" "firehose_processor" {
  name               = "firehose-cwl-log-processor-staging"
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
  name   = "firehose-cwl-log-processor-staging"
  role   = "firehose-cwl-log-processor-staging"
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

}

resource "aws_cloudwatch_log_group" "firehose_cwl_processor" {
  name = "/aws/lambda/Firehose-CWL-Processor"
}
