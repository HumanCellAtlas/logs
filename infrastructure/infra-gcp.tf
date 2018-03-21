variable "gcp_pubsub_authorized_service_accounts" {
  type = "list"
}

variable "gcp_log_topic_subscription_name" {}
variable "gcp_logs_project_name" {}

resource "google_project" "logs" {
  project_id = "${var.gcp_logs_project_name}"
  name = "${var.gcp_logs_project_name}"
}

resource "google_pubsub_topic" "logs" {
  name = "logs"
}

data "google_iam_policy" "pubsub_publisher" {
  binding {
    role = "roles/pubsub.publisher"
    members = ["${formatlist("serviceAccount:%s", var.gcp_pubsub_authorized_service_accounts)}"]
  }
}

resource "google_pubsub_topic_iam_policy" "publisher" {
  topic = "${google_pubsub_topic.logs.name}"
  policy_data = "${data.google_iam_policy.pubsub_publisher.policy_data}"
}

resource "google_pubsub_subscription" "logs" {
  name = "${var.gcp_log_topic_subscription_name}"
  topic = "${google_pubsub_topic.logs.name}"
  project = "${var.gcp_logs_project_name}"
}