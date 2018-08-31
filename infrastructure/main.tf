variable "aws_profile" {}

variable "aws_region" {
  default = "us-east-1"
}

variable "gcp_region" {
  default = "us-central1"
}

provider "aws" {
  region = "${var.aws_region}"
  profile = "${var.aws_profile}"
}

provider "google" {
  region = "${var.gcp_region}"
}

// the bucket must be configured with the -backend-config flag on `terraform init`
terraform {
  backend "s3" {
    key = "logs/terraform.tfstate"
  }
}

resource "aws_s3_bucket" "lambda_area_bucket" {
  bucket = "org-hca-logs-lambda-deployment-${var.account_id}"
  acl = "private"
  force_destroy = "false"
  acceleration_status = "Enabled"
}