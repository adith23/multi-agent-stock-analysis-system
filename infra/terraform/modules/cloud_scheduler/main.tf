resource "google_cloud_scheduler_job" "job" {
  for_each         = var.jobs
  project          = var.project_id
  region           = var.region
  name             = each.key
  description      = "Consolidated stock analysis schedule: ${each.value.schedule_name}"
  schedule         = each.value.schedule
  time_zone        = each.value.time_zone
  attempt_deadline = "180s"

  retry_config {
    retry_count          = 3
    min_backoff_duration = "10s"
    max_backoff_duration = "300s"
    max_doublings        = 3
  }

  http_target {
    http_method = "POST"
    uri         = "${var.backend_uri}/api/internal/scheduler/${each.value.schedule_name}/"
    headers     = { "Content-Type" = "application/json" }
    body        = base64encode("{}")
    oidc_token {
      service_account_email = var.service_account_email
      audience              = var.backend_uri
    }
  }
}
