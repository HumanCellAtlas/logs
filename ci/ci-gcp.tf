variable "gcp_logs_project_name" {}

resource "google_service_account" "ci" {
  account_id   = "${var.travis_user}"
  display_name = "${var.travis_user}"
}

resource "google_project_iam_binding" "ci" {
  project = "${var.gcp_logs_project_name}"
  role = "roles/pubsub.admin"
  members = ["serviceAccount:${google_service_account.ci.email}"]
}

