output "artifact_registry_url" { value = module.artifact_registry.repository_url }
output "ml_models_bucket" { value = module.storage.bucket_name }
output "backend_url" { value = var.create_runtime_services ? module.backend[0].uri : local.backend_uri }
output "frontend_url" { value = var.create_runtime_services ? module.frontend[0].uri : local.frontend_uri }
output "worker_url" { value = var.create_runtime_services ? module.worker[0].uri : local.worker_uri }
output "cloud_build_service_account" { value = module.iam.service_account_emails.cloud_build }
output "cloud_build_ci_service_account" { value = module.iam.service_account_emails.cloud_build_ci }
output "secret_names" { value = sort(tolist(local.secret_ids)) }
