locals {
  display_names = {
    cloud_run       = "Stock Analysis Cloud Run"
    cloud_tasks     = "Stock Analysis Cloud Tasks Invoker"
    cloud_scheduler = "Stock Analysis Cloud Scheduler Invoker"
    cloud_build     = "Stock Analysis Cloud Build"
    cloud_build_ci  = "Stock Analysis Cloud Build CI"
  }
}

resource "google_service_account" "service_account" {
  for_each     = var.service_account_ids
  project      = var.project_id
  account_id   = each.value
  display_name = local.display_names[each.key]
}

locals {
  project_roles = {
    cloud_run_tasks_enqueuer = {
      role = "roles/cloudtasks.enqueuer"
      sa   = "cloud_run"
    }
    cloud_build_run_admin = {
      role = "roles/run.admin"
      sa   = "cloud_build"
    }
    cloud_build_logging_writer = {
      role = "roles/logging.logWriter"
      sa   = "cloud_build"
    }
    cloud_build_ci_logging_writer = {
      role = "roles/logging.logWriter"
      sa   = "cloud_build_ci"
    }
  }
}

resource "google_project_iam_member" "project_role" {
  for_each = local.project_roles
  project  = var.project_id
  role     = each.value.role
  member   = "serviceAccount:${google_service_account.service_account[each.value.sa].email}"
}

resource "google_service_account_iam_member" "cloud_build_acts_as_cloud_run" {
  service_account_id = google_service_account.service_account["cloud_run"].name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.service_account["cloud_build"].email}"
}

resource "google_service_account_iam_member" "cloud_run_acts_as_cloud_tasks" {
  service_account_id = google_service_account.service_account["cloud_tasks"].name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.service_account["cloud_run"].email}"
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_service_account_iam_member" "cloud_build_service_agent" {
  for_each = toset(["cloud_build", "cloud_build_ci"])

  service_account_id = google_service_account.service_account[each.value].name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
}
