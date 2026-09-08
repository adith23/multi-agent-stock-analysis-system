variable "project_id" { type = string }
variable "region" { type = string }
variable "bucket_name" { type = string }
variable "labels" {
  type    = map(string)
  default = {}
}
