variable "region" {}
variable "account_id" {}
variable "terraform_bucket" {}
variable "travis_user" {}
variable "aws_profile" {}

provider "aws" {
    region = "${var.region}"
    profile = "${var.aws_profile}"
}

////
// general setup
//

// the bucket must be configured with the -backend-config flag on `terraform init`
terraform {
    backend "s3" {
        key = "logs/ci-terraform.tfstate"
    }
}


resource "aws_iam_user" "logs-travis" {
    name = "${var.travis_user}"
    path = "/"
}


resource "aws_iam_policy" "CloudWatchLogsWriter" {
    name        = "CloudWatchLogsWriter"
    path        = "/"
    description = ""
    policy      = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:ListTagsLogGroup",
        "logs:DeleteSubscriptionFilter",
        "logs:DescribeLogStreams",
        "logs:CreateExportTask",
        "logs:CreateLogStream",
        "logs:TagLogGroup",
        "logs:DeleteLogGroup",
        "logs:CancelExportTask",
        "logs:AssociateKmsKey",
        "logs:PutDestination",
        "logs:DisassociateKmsKey",
        "logs:UntagLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutDestinationPolicy",
        "logs:PutLogEvents",
        "logs:CreateLogGroup",
        "logs:PutMetricFilter",
        "logs:PutResourcePolicy",
        "logs:PutSubscriptionFilter",
        "logs:PutRetentionPolicy"
      ],
      "Resource": "*"
    }
  ]
}
POLICY
}

resource "aws_iam_policy" "LogsS3Policy" {
    name        = "LogsS3Policy"
    path        = "/"
    description = ""
    policy      = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::${var.terraform_bucket}/logs/*",
        "arn:aws:s3:::kinesis-es-firehose-failures-${var.account_id}",
        "arn:aws:s3:::${var.account_id}-cloudtrail"
      ]
    }
  ]
}
POLICY
}

resource "aws_iam_policy" "CloudFormationAlertStackReadAccess" {
    name        = "CloudFormationAlertStackReadAccess"
    path        = "/"
    description = ""
    policy      = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:GetTemplate",
        "cloudformation:DescribeStacks"
      ],
      "Resource": "arn:aws:cloudformation:${var.region}:${var.account_id}:stack/CloudTrail-Monitoring/*"
    }
  ]
}
POLICY
}


resource "aws_iam_policy" "LogsFirehoseLambda" {
    name        = "LogsFirehoseLambda"
    path        = "/"
    description = ""
    policy      = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateEventSourceMapping",
        "lambda:ListFunctions",
        "lambda:GetEventSourceMapping",
        "lambda:ListEventSourceMappings",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetAccountSettings",
        "lambda:CreateEventSourceMapping",
        "lambda:DeleteEventSourceMapping"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "lambda:*",
      "Resource": "arn:aws:lambda:${var.region}:${var.account_id}:function:Firehose-CWL-Processor"
    }
  ]
}
POLICY
}


resource "aws_iam_policy" "LogsFirehosePolicy" {
    name        = "LogsFirehosePolicy"
    path        = "/"
    description = ""
    policy      = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "firehose:*",
      "Resource": "arn:aws:firehose:${var.region}:${var.account_id}:deliverystream/Kinesis-Firehose-ELK"
    }
  ]
}
POLICY
}


resource "aws_iam_policy" "TravisIAMSubscription" {
    name        = "TravisIAMSubscription"
    path        = "/"
    description = ""
    policy      = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "iam:PassRole",
        "logs:PutSubscriptionFilter",
        "logs:DescribeSubscriptionFilters",
        "logs:DeleteSubscriptionFilter",
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:*:*:*",
        "arn:aws:iam::${var.account_id}:role/cwl-firehose"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeSubscriptionFilter",
        "logs:CreateLogGroup"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
POLICY
}

resource "aws_iam_policy" "LogsCIAccess" {
    name        = "LogsCIAccess"
    path        = "/"
    description = ""
    policy      = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:GetPolicyVersion",
        "iam:GetPolicy",
        "lambda:ListFunctions",
        "cloudtrail:GetTrailStatus",
        "sns:GetSubscriptionAttributes",
        "cloudtrail:GetEventSelectors",
        "s3:ListObjects",
        "cloudtrail:DescribeTrails",
        "s3:ListAllMyBuckets",
        "lambda:ListTags",
        "cloudtrail:ListTags",
        "s3:HeadBucket",
        "iam:GetRolePolicy"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:GetTopicAttributes"
      ],
      "Resource": [
        "arn:aws:sns:${var.region}:${var.account_id}:cloudwatch-alarms"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "events:DescribeRule",
        "events:ListTargetsByRule"
      ],
      "Resource": [
        "arn:aws:events:${var.region}:${var.account_id}:rule/capture_create_log_group",
        "arn:aws:events:${var.region}:${var.account_id}:rule/handler"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:ListVersionsByFunction",
        "lambda:GetFunction",
        "lambda:GetPolicy",
        "lambda:GetFunctionConfiguration"
      ],
      "Resource": [
        "arn:aws:lambda:${var.region}:${var.account_id}:function:cloudwatch-slack-notifications",
        "arn:aws:lambda:${var.region}:${var.account_id}:function:es-idx-manager-*",
        "arn:aws:lambda:${var.region}:${var.account_id}:function:gcp-to-cwl-exporter-*",
        "arn:aws:lambda:${var.region}:${var.account_id}:function:cwl_firehose_subscriber"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::org-humancellatlas-${var.account_id}-terraform",
        "arn:aws:s3:::org-humancellatlas-${var.account_id}-terraform/logs/terraform.tfstate"
      ]
    }
  ]
}
POLICY
}


resource "aws_iam_policy" "LogsElasticsearchFullAccess" {
    name        = "LogsElasticsearchFullAccess"
    path        = "/"
    description = ""
    policy      = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "es:ListTags",
      "Resource": "arn:aws:es:${var.region}:${var.account_id}:domain/*"
    },
    {
      "Effect": "Allow",
      "Action": "es:*",
      "Resource": "arn:aws:es:${var.region}:${var.account_id}:domain/hca-logs"
    }
  ]
}
POLICY
}

resource "aws_iam_policy_attachment" "CloudFormationAlertStackReadAccess-policy-attachment" {
    name       = "CloudFormationAlertStackReadAccess-policy-attachment"
    policy_arn = "arn:aws:iam::${var.account_id}:policy/CloudFormationAlertStackReadAccess"
    groups     = []
    users      = ["${aws_iam_user.logs-travis.name}"]
    roles      = []
    depends_on = [
        "aws_iam_policy.CloudFormationAlertStackReadAccess",
        "aws_iam_user.logs-travis"
    ]
}

resource "aws_iam_policy_attachment" "CloudWatchLogsWriter-policy-attachment" {
    name       = "CloudWatchLogsWriter-policy-attachment"
    policy_arn = "arn:aws:iam::${var.account_id}:policy/CloudWatchLogsWriter"
    users      = ["${aws_iam_user.logs-travis.name}"]
    depends_on = [
        "aws_iam_policy.CloudWatchLogsWriter",
        "aws_iam_user.logs-travis"
    ]
}

resource "aws_iam_policy_attachment" "LogsCIAccess-policy-attachment" {
    name       = "LogsCIAccess-policy-attachment"
    policy_arn = "arn:aws:iam::${var.account_id}:policy/LogsCIAccess"
    groups     = []
    users      = ["${aws_iam_user.logs-travis.name}"]
    roles      = []
    depends_on = [
        "aws_iam_policy.LogsCIAccess",
        "aws_iam_user.logs-travis"
    ]
}

resource "aws_iam_policy_attachment" "LogsElasticsearchFullAccess-policy-attachment" {
    name       = "LogsElasticsearchFullAccess-policy-attachment"
    policy_arn = "arn:aws:iam::${var.account_id}:policy/LogsElasticsearchFullAccess"
    groups     = []
    users      = ["${aws_iam_user.logs-travis.name}"]
    roles      = []
    depends_on = [
        "aws_iam_policy.LogsElasticsearchFullAccess",
        "aws_iam_user.logs-travis"
    ]
}

resource "aws_iam_policy_attachment" "LogsFirehoseLambda-policy-attachment" {
    name       = "LogsFirehoseLambda-policy-attachment"
    policy_arn = "arn:aws:iam::${var.account_id}:policy/LogsFirehoseLambda"
    groups     = []
    users      = ["${aws_iam_user.logs-travis.name}"]
    roles      = []
    depends_on = [
        "aws_iam_policy.LogsFirehoseLambda",
        "aws_iam_user.logs-travis"
    ]
}

resource "aws_iam_policy_attachment" "LogsFirehosePolicy-policy-attachment" {
    name       = "LogsFirehosePolicy-policy-attachment"
    policy_arn = "arn:aws:iam::${var.account_id}:policy/LogsFirehosePolicy"
    groups     = []
    users      = ["${aws_iam_user.logs-travis.name}"]
    roles      = []
    depends_on = [
        "aws_iam_policy.LogsFirehosePolicy",
        "aws_iam_user.logs-travis"
    ]
}

resource "aws_iam_policy_attachment" "TravisIAMSubscription-policy-attachment" {
    name       = "TravisIAMSubscription-policy-attachment"
    policy_arn = "arn:aws:iam::${var.account_id}:policy/TravisIAMSubscription"
    groups     = []
    users      = ["${aws_iam_user.logs-travis.name}"]
    roles      = []
    depends_on = [
        "aws_iam_policy.TravisIAMSubscription",
        "aws_iam_user.logs-travis"
    ]
}

resource "aws_iam_policy_attachment" "LogsS3Policy-policy-attachment" {
    name       = "LogsS3Policy-policy-attachment"
    policy_arn = "arn:aws:iam::${var.account_id}:policy/LogsS3Policy"
    groups     = []
    users      = ["${aws_iam_user.logs-travis.name}"]
    roles      = []
    depends_on = [
        "aws_iam_policy.LogsS3Policy",
        "aws_iam_user.logs-travis"
    ]
}
