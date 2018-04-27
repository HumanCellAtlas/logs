variable "aws_profile" {}
variable "es_endpoint" {}
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
    key = "es_idx_manager/app.tfstate"
  }
}

////
//  Health check app
//

resource "aws_iam_role" "es_idx_manager" {
  name = "es-idx-manager"
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

resource "aws_iam_role_policy" "es_idx_manager" {
  name   = "es-idx-manager"
  role   = "${aws_iam_role.es_idx_manager.name}"
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
            "Action": "es:*",
            "Resource": "arn:aws:es:*:*:*"
        }
    ]
}
EOF
  depends_on = [
    "aws_iam_role.es_idx_manager"
  ]
}

data "archive_file" "lambda_zip" {
  type = "zip"
  source_dir = "./target"
  output_path = "./lambda.zip"
}

resource "aws_lambda_function" "es_idx_manager" {
  function_name = "es-idx-manager"
  description = "Manages hca log elasticsearch indexes"
  filename = "${data.archive_file.lambda_zip.output_path}"
  role = "${aws_iam_role.es_idx_manager.arn}"
  handler = "app.handler"
  runtime = "python3.6"
  memory_size = 256
  timeout = 120
  source_code_hash = "${base64sha256(file("${data.archive_file.lambda_zip.output_path}"))}"
  environment {
    variables = {
      ES_IDX_MANAGER_SETTINGS = "./es-idx-manager-settings.yaml"
    }
  }
  depends_on = [
    "data.archive_file.lambda_zip"
  ]
}


////
//  Timer
//

resource "aws_cloudwatch_event_rule" "es_idx_manager" {
  name = "es-idx-manager"
  description = "Trigger the es-idx-manager app"
  schedule_expression = "rate(12 hours)"
}

resource "aws_lambda_permission" "dss" {
  statement_id = "AllowExecutionFromCloudWatch"
  principal = "events.amazonaws.com"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.es_idx_manager.function_name}"
  source_arn = "${aws_cloudwatch_event_rule.es_idx_manager.arn}"
  depends_on = [
    "aws_lambda_function.es_idx_manager"
  ]
}

resource "aws_cloudwatch_event_target" "dss" {
  rule      = "${aws_cloudwatch_event_rule.es_idx_manager.name}"
  target_id = "invoke-es-idx-manager"
  arn       = "${aws_lambda_function.es_idx_manager.arn}"
}

output "es_conf_file" {
  value = <<EOF
- name: elastic search human cell atlas
  endpoint: ${var.es_endpoint}
  days: 7
  index_format: '%Y-%m-%d'
  indices:
    - prefix: cwl

- name: test configuration
  endpoint: ${var.es_endpoint}
  days: 7
  index_format: '%Y-%m-%d'
  indices:
    - prefix: test
EOF
}
