variable "gcp_pubsub_authorized_service_accounts" {
  type = "list"
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