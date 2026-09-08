output "uptime_check_id" { value = google_monitoring_uptime_check_config.backend.uptime_check_id }
output "dashboard_id" { value = google_monitoring_dashboard.operations.id }
