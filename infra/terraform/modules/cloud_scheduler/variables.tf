variable "project_id" { type = string }
variable "region" { type = string }
variable "backend_uri" { type = string }
variable "service_account_email" { type = string }
variable "jobs" {
  type = map(object({
    schedule      = string
    schedule_name = string
    time_zone     = string
  }))
}
