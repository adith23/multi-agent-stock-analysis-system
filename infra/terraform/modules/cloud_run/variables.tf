variable "project_id" { type = string }
variable "region" { type = string }
variable "name" { type = string }
variable "image" { type = string }
variable "service_account_email" { type = string }
variable "container_port" { type = number }
variable "cpu" { type = string }
variable "memory" { type = string }
variable "min_instances" { type = number }
variable "max_instances" { type = number }
variable "concurrency" { type = number }
variable "timeout" { type = string }
variable "ingress" {
  type    = string
  default = "INGRESS_TRAFFIC_ALL"
}
variable "allow_unauthenticated" {
  type    = bool
  default = false
}
variable "environment_variables" {
  type    = map(string)
  default = {}
}
variable "secret_environment_variables" {
  type    = map(string)
  default = {}
}
variable "startup_probe_path" {
  type    = string
  default = "/api/v1/health/live/"
}
variable "labels" {
  type    = map(string)
  default = {}
}
