resource "google_monitoring_uptime_check_config" "backend" {
  project      = var.project_id
  display_name = "Stock Analysis Backend Liveness"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path           = "/api/v1/health/live/"
    port           = 443
    use_ssl        = true
    validate_ssl   = true
    request_method = "GET"
  }
  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.backend_host
    }
  }
}

resource "google_monitoring_notification_channel" "email" {
  count        = var.alert_email == "" ? 0 : 1
  project      = var.project_id
  display_name = "Stock Analysis Operations Email"
  type         = "email"
  labels       = { email_address = var.alert_email }
}

resource "google_monitoring_alert_policy" "uptime" {
  project      = var.project_id
  display_name = "Stock Analysis Backend Unavailable"
  combiner     = "OR"

  conditions {
    display_name = "Liveness check failed"
    condition_threshold {
      filter = join(" AND ", [
        "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\"",
        "resource.type=\"uptime_url\"",
        "metric.label.check_id=\"${google_monitoring_uptime_check_config.backend.uptime_check_id}\"",
      ])
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_FRACTION_TRUE"
      }
    }
  }

  notification_channels = var.alert_email == "" ? [] : [google_monitoring_notification_channel.email[0].name]
  alert_strategy { auto_close = "1800s" }
}

resource "google_monitoring_alert_policy" "backend_errors" {
  project      = var.project_id
  display_name = "Stock Analysis Backend 5xx Volume"
  combiner     = "OR"

  conditions {
    display_name = "More than five 5xx responses in five minutes"
    condition_threshold {
      filter = join(" AND ", [
        "resource.type=\"cloud_run_revision\"",
        "metric.type=\"run.googleapis.com/request_count\"",
        "metric.label.response_code_class=\"5xx\"",
        "resource.label.service_name=\"backend-api\"",
      ])
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.label.service_name"]
      }
      trigger { count = 1 }
    }
  }

  notification_channels = var.alert_email == "" ? [] : [google_monitoring_notification_channel.email[0].name]
  alert_strategy { auto_close = "1800s" }
}

resource "google_monitoring_dashboard" "operations" {
  project = var.project_id
  dashboard_json = jsonencode({
    displayName = "Stock Analysis Operations"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          xPos = 0, yPos = 0, width = 6, height = 4
          widget = {
            title = "Cloud Run request latency (P95)"
            xyChart = {
              dataSets = [{
                plotType = "LINE"
                timeSeriesQuery = { timeSeriesFilter = {
                  filter      = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\""
                  aggregation = { alignmentPeriod = "300s", perSeriesAligner = "ALIGN_PERCENTILE_95" }
                } }
              }]
              yAxis = { label = "Latency", scale = "LINEAR" }
            }
          }
        },
        {
          xPos = 6, yPos = 0, width = 6, height = 4
          widget = {
            title = "Cloud Run instance count"
            xyChart = {
              dataSets = [{
                plotType = "LINE"
                timeSeriesQuery = { timeSeriesFilter = {
                  filter      = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/instance_count\""
                  aggregation = { alignmentPeriod = "300s", perSeriesAligner = "ALIGN_MEAN" }
                } }
              }]
              yAxis = { label = "Instances", scale = "LINEAR" }
            }
          }
        },
        {
          xPos = 0, yPos = 4, width = 6, height = 4
          widget = {
            title = "Cloud Tasks queue depth"
            xyChart = {
              dataSets = [{
                plotType = "LINE"
                timeSeriesQuery = { timeSeriesFilter = {
                  filter      = "resource.type=\"cloud_tasks_queue\" AND metric.type=\"cloudtasks.googleapis.com/queue/depth\""
                  aggregation = { alignmentPeriod = "300s", perSeriesAligner = "ALIGN_MAX" }
                } }
              }]
              yAxis = { label = "Tasks", scale = "LINEAR" }
            }
          }
        },
        {
          xPos = 6, yPos = 4, width = 6, height = 4
          widget = {
            title = "Cloud Run memory utilization"
            xyChart = {
              dataSets = [{
                plotType = "LINE"
                timeSeriesQuery = { timeSeriesFilter = {
                  filter      = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/memory/utilizations\""
                  aggregation = { alignmentPeriod = "300s", perSeriesAligner = "ALIGN_PERCENTILE_95" }
                } }
              }]
              yAxis = { label = "Utilization", scale = "LINEAR" }
            }
          }
        },
      ]
    }
  })
}
