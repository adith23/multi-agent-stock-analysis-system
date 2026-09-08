resource "google_secret_manager_secret" "application" {
  for_each  = var.secret_ids
  project   = var.project_id
  secret_id = each.value
  labels    = var.labels

  replication {
    auto {}
  }
}

locals {
  bindings = {
    for pair in setproduct(var.secret_ids, var.accessor_service_accounts) :
    "${pair[0]}:${pair[1]}" => { secret = pair[0], service_account = pair[1] }
  }
}

resource "google_secret_manager_secret_iam_member" "accessor" {
  for_each  = local.bindings
  project   = var.project_id
  secret_id = google_secret_manager_secret.application[each.value.secret].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${each.value.service_account}"
}
