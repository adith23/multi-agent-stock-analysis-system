variable "project_id" { type = string }
variable "region" { type = string }
variable "queues" {
  type = map(object({
    max_dispatches_per_second = number
    max_concurrent_dispatches = number
  }))
}
