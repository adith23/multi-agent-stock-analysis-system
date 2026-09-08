resource "google_artifact_registry_repository" "docker" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repository_id
  description   = "Multi-agent stock analysis container images"
  format        = "DOCKER"
  labels        = var.labels

  cleanup_policy_dry_run = false
  cleanup_policies {
    id     = "delete-images-older-than-seven-days"
    action = "DELETE"
    condition {
      tag_state  = "ANY"
      older_than = "604800s"
    }
  }
  cleanup_policies {
    id     = "keep-three-recent-versions"
    action = "KEEP"
    most_recent_versions {
      keep_count = 3
    }
  }
}
