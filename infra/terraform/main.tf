provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_project" "current" {
  project_id = var.project_id
}

locals {
  required_apis = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "cloudtasks.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
  ])
  common_labels = merge(var.labels, {
    application = "stock-analysis"
    environment = var.environment
    managed_by  = "terraform"
  })
  repository_id = "stock-analysis"
  backend_name  = "backend-api"
  frontend_name = "frontend"
  worker_name   = "task-worker"
  # Cloud Run's stable service URL is deterministic for a project and region.
  backend_uri    = "https://${local.backend_name}-${data.google_project.current.number}.${var.region}.run.app"
  frontend_uri   = "https://${local.frontend_name}-${data.google_project.current.number}.${var.region}.run.app"
  worker_uri     = "https://${local.worker_name}-${data.google_project.current.number}.${var.region}.run.app"
  backend_image  = "${var.region}-docker.pkg.dev/${var.project_id}/${local.repository_id}/backend:${var.image_tag}"
  frontend_image = "${var.region}-docker.pkg.dev/${var.project_id}/${local.repository_id}/frontend:${var.image_tag}"
  secret_ids     = toset(["stock-analysis-env"])
  runtime_secrets = {
    APP_SECRETS_JSON = "stock-analysis-env"
  }
}

resource "google_project_service" "required" {
  for_each           = local.required_apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

module "iam" {
  source     = "./modules/iam"
  project_id = var.project_id
  service_account_ids = {
    cloud_run       = "cloud-run-sa"
    cloud_tasks     = "cloud-tasks-sa"
    cloud_scheduler = "cloud-scheduler-sa"
    cloud_build     = "cloud-build-sa"
    cloud_build_ci  = "cloud-build-ci-sa"
  }
  depends_on = [google_project_service.required]
}

module "artifact_registry" {
  source        = "./modules/artifact_registry"
  project_id    = var.project_id
  region        = var.region
  repository_id = local.repository_id
  labels        = local.common_labels
  depends_on    = [google_project_service.required]
}

module "storage" {
  source      = "./modules/storage"
  project_id  = var.project_id
  region      = var.region
  bucket_name = "${var.project_id}-ml-models"
  labels      = local.common_labels
  depends_on  = [google_project_service.required]
}

module "secrets" {
  source     = "./modules/secrets"
  project_id = var.project_id
  secret_ids = local.secret_ids
  labels     = local.common_labels
  accessor_service_accounts = [
    module.iam.service_account_emails.cloud_run,
  ]
  depends_on = [google_project_service.required]
}

module "cloud_tasks" {
  source     = "./modules/cloud_tasks"
  project_id = var.project_id
  region     = var.region
  queues = {
    default      = { max_dispatches_per_second = 5, max_concurrent_dispatches = 10 }
    orchestrator = { max_dispatches_per_second = 1, max_concurrent_dispatches = 1 }
    agents       = { max_dispatches_per_second = 2, max_concurrent_dispatches = 4 }
    computation  = { max_dispatches_per_second = 2, max_concurrent_dispatches = 4 }
    ingestion    = { max_dispatches_per_second = 2, max_concurrent_dispatches = 4 }
  }
  depends_on = [google_project_service.required]
}

resource "google_storage_bucket_iam_member" "model_viewer" {
  bucket = module.storage.bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${module.iam.service_account_emails.cloud_run}"
}

resource "google_artifact_registry_repository_iam_member" "cloud_build_writer" {
  project    = var.project_id
  location   = var.region
  repository = module.artifact_registry.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${module.iam.service_account_emails.cloud_build}"
}

locals {
  backend_environment = {
    DJANGO_SETTINGS_MODULE                = "config.settings.production"
    DJANGO_ALLOWED_HOSTS                  = ".run.app"
    DJANGO_SECURE_SSL_REDIRECT            = "False"
    CORS_ALLOWED_ORIGINS                  = local.frontend_uri
    TASK_BACKEND                          = "cloud_tasks"
    GCP_PROJECT_ID                        = var.project_id
    GCP_LOCATION                          = var.region
    CLOUD_RUN_BACKEND_URL                 = local.backend_uri
    CLOUD_RUN_WORKER_URL                  = local.worker_uri
    CLOUD_TASKS_SA_EMAIL                  = module.iam.service_account_emails.cloud_tasks
    CLOUD_SCHEDULER_SA_EMAIL              = module.iam.service_account_emails.cloud_scheduler
    CLOUD_TASKS_DISPATCH_DEADLINE_SECONDS = "1800"
    GCS_ML_MODELS_BUCKET                  = module.storage.bucket_name
    LOG_LEVEL                             = "INFO"
    LLM_PROVIDER                          = "gemini"
    LLM_DEFAULT_MODEL                     = var.llm_default_model
    LLM_TEMPERATURE                       = "0.3"
    SEC_EDGAR_IDENTITY                    = var.sec_edgar_identity
  }
}

module "backend" {
  count                 = var.create_runtime_services ? 1 : 0
  source                = "./modules/cloud_run"
  project_id            = var.project_id
  region                = var.region
  name                  = local.backend_name
  image                 = local.backend_image
  service_account_email = module.iam.service_account_emails.cloud_run
  container_port        = 8000
  cpu                   = "1"
  memory                = "512Mi"
  min_instances         = 0
  max_instances         = 2
  concurrency           = 40
  timeout               = "300s"
  allow_unauthenticated = true
  environment_variables = merge(local.backend_environment, {
    WEB_CONCURRENCY          = "2"
    GUNICORN_TIMEOUT_SECONDS = "300"
  })
  secret_environment_variables = local.runtime_secrets
  labels                       = local.common_labels
  depends_on                   = [module.artifact_registry, module.secrets]
}

module "worker" {
  count                 = var.create_runtime_services ? 1 : 0
  source                = "./modules/cloud_run"
  project_id            = var.project_id
  region                = var.region
  name                  = local.worker_name
  image                 = local.backend_image
  service_account_email = module.iam.service_account_emails.cloud_run
  container_port        = 8000
  cpu                   = "1"
  memory                = "1Gi"
  min_instances         = 0
  max_instances         = 4
  concurrency           = 1
  timeout               = "1800s"
  ingress               = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  allow_unauthenticated = false
  environment_variables = merge(local.backend_environment, {
    WEB_CONCURRENCY          = "1"
    GUNICORN_TIMEOUT_SECONDS = "1800"
  })
  secret_environment_variables = local.runtime_secrets
  labels                       = local.common_labels
  depends_on                   = [module.artifact_registry, module.secrets]
}

module "frontend" {
  count                 = var.create_runtime_services ? 1 : 0
  source                = "./modules/cloud_run"
  project_id            = var.project_id
  region                = var.region
  name                  = local.frontend_name
  image                 = local.frontend_image
  service_account_email = module.iam.service_account_emails.cloud_run
  container_port        = 3000
  cpu                   = "1"
  memory                = "256Mi"
  min_instances         = 0
  max_instances         = 2
  concurrency           = 80
  timeout               = "60s"
  allow_unauthenticated = true
  environment_variables = {
    NEXT_PUBLIC_API_BASE_URL = "${local.backend_uri}/api/v1"
    NEXT_PUBLIC_SSE_BASE_URL = "${local.backend_uri}/api/v1"
  }
  labels     = local.common_labels
  depends_on = [module.artifact_registry]
}

resource "google_cloud_run_v2_job" "migration" {
  count               = var.create_runtime_services ? 1 : 0
  project             = var.project_id
  name                = "db-migrate"
  location            = var.region
  deletion_protection = false
  labels              = local.common_labels

  template {
    template {
      service_account = module.iam.service_account_emails.cloud_run
      timeout         = "600s"
      max_retries     = 1
      containers {
        image   = local.backend_image
        command = ["python"]
        args    = ["manage.py", "migrate", "--noinput"]
        resources { limits = { cpu = "1", memory = "512Mi" } }
        dynamic "env" {
          for_each = local.backend_environment
          content {
            name  = env.key
            value = env.value
          }
        }
        dynamic "env" {
          for_each = local.runtime_secrets
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value
                version = "latest"
              }
            }
          }
        }
      }
    }
  }
  depends_on = [module.secrets, module.artifact_registry]
}

resource "google_cloud_run_v2_service_iam_member" "tasks_invokes_worker" {
  count    = var.create_runtime_services ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = module.worker[0].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${module.iam.service_account_emails.cloud_tasks}"
}

resource "google_cloud_run_v2_service_iam_member" "scheduler_invokes_backend" {
  count    = var.create_runtime_services ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = module.backend[0].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${module.iam.service_account_emails.cloud_scheduler}"
}

module "scheduler" {
  count                 = var.create_runtime_services ? 1 : 0
  source                = "./modules/cloud_scheduler"
  project_id            = var.project_id
  region                = var.region
  backend_uri           = module.backend[0].uri
  service_account_email = module.iam.service_account_emails.cloud_scheduler
  jobs = {
    market-data-hourly   = { schedule = "0 * * * *", schedule_name = "market-data-hourly", time_zone = "UTC" }
    reference-data-daily = { schedule = "0 2 * * *", schedule_name = "reference-data-daily", time_zone = "UTC" }
    portfolio-monitors   = { schedule = "*/5 * * * *", schedule_name = "portfolio-monitors", time_zone = "UTC" }
  }
  depends_on = [google_cloud_run_v2_service_iam_member.scheduler_invokes_backend]
}

module "monitoring" {
  count        = var.create_runtime_services ? 1 : 0
  source       = "./modules/monitoring"
  project_id   = var.project_id
  backend_host = trimsuffix(trimprefix(module.backend[0].uri, "https://"), "/")
  alert_email  = var.alert_email
  depends_on   = [module.backend]
}
