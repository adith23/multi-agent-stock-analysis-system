variable "project_id" {
  description = "GCP project that owns the deployment."
  type        = string
}

variable "region" {
  description = "Always Free eligible US region for regional services."
  type        = string
  default     = "us-central1"

  validation {
    condition     = contains(["us-central1", "us-east1", "us-west1"], var.region)
    error_message = "Use us-central1, us-east1, or us-west1 to remain in Always Free eligible regions."
  }
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "production"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be staging or production."
  }
}

variable "image_tag" {
  description = "Immutable backend/frontend image tag already present in Artifact Registry."
  type        = string
  default     = "latest"
}

variable "create_runtime_services" {
  description = "Create Cloud Run services, migration job, Scheduler jobs, and monitoring after images and secret versions exist."
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Optional email address for Monitoring alerts."
  type        = string
  default     = ""
}

variable "sec_edgar_identity" {
  description = "SEC-compliant application identity, for example Name email@example.com."
  type        = string
  default     = ""
}

variable "llm_default_model" {
  description = "Default Gemini model name."
  type        = string
  default     = "gemini-3.1-flash-lite"
}

variable "labels" {
  description = "Additional labels applied to supported resources."
  type        = map(string)
  default     = {}
}
