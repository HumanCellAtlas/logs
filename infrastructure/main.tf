variable "aws_region" {
  default = "us-east-1"
}

variable "gcp_region" {
  default = "us-central1"
}

provider "aws" {
  region = "${var.aws_region}"
  profile = "hca"
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

