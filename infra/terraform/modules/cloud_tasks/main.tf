resource "google_cloud_tasks_queue" "queue" {
  for_each = var.queues
  project  = var.project_id
  location = var.region
  name     = each.key

  rate_limits {
    max_dispatches_per_second = each.value.max_dispatches_per_second
    max_concurrent_dispatches = each.value.max_concurrent_dispatches
  }
  retry_config {
    max_attempts       = 3
    max_retry_duration = "3600s"
    min_backoff        = "10s"
    max_backoff        = "300s"
    max_doublings      = 4
  }
  stackdriver_logging_config { sampling_ratio = 0.1 }
}
