# GCP deployment guide

This guide deploys the application to Cloud Run with Cloud Tasks and Cloud
Scheduler while retaining Celery and Docker Compose for local development. It
is designed to stay inside GCP Always Free allowances at low traffic, but free
tier eligibility is not a spending cap. Enable billing alerts and inspect GCP's
current pricing before every production launch.

## Architecture and trust boundaries

```text
Browser -> public frontend Cloud Run service
Browser -> public backend Cloud Run service -> Django JWT/CORS/throttling
Backend -> Cloud Tasks -> private worker Cloud Run service (OIDC)
Cloud Scheduler -> backend internal routes (OIDC) -> Cloud Tasks
Backend/worker -> Neon PostgreSQL, Redis Cloud, private model GCS bucket
Cloud Build -> Artifact Registry, migration job, Cloud Run services
```

The backend must be invokable without Cloud Run IAM credentials because the
browser calls it directly. Public invocation does not make application data
public: protected API routes still require Django JWT/session authentication.
Only liveness, readiness, auth, and the API's intentionally public surfaces are
anonymous. The task worker has internal ingress, no `allUsers` binding, a task
allowlist, service-account OIDC validation, body limits, and replay suppression.

## Prerequisites

- A GCP project with billing enabled and `gcloud` authenticated as an owner or
  bootstrap administrator.
- Terraform 1.7 or newer.
- A Neon PostgreSQL connection URL with `sslmode=require`.
- A Redis Cloud TLS URL (`rediss://`) sized within its connection/memory limit.
- Required market-data and Gemini API credentials.
- A GitHub repository connected to Cloud Build through the Google Cloud console.

Use `us-central1`, `us-east1`, or `us-west1`; the Terraform region validation
prevents accidental selection of a region outside the plan's Always Free scope.

## 1. Create the remote-state bucket

This bucket is intentionally outside the Terraform state it stores. Bucket
names are global, so replace `PROJECT_ID`.

```powershell
$ProjectId = "PROJECT_ID"
gcloud config set project $ProjectId
gcloud storage buckets create "gs://$ProjectId-tf-state" `
  --location=us-central1 `
  --uniform-bucket-level-access `
  --public-access-prevention
```

Keep object versioning/retention policy appropriate to your recovery policy.
Do not run `terraform destroy` against the state bucket.

## 2. Apply the foundation

Copy the examples without committing the resulting files:

```powershell
Copy-Item infra/terraform/environments/production/backend.hcl.example infra/terraform/backend.hcl
Copy-Item infra/terraform/environments/production/terraform.tfvars.example infra/terraform/terraform.tfvars
```

Set `project_id`, set `create_runtime_services = false`, then run:

```powershell
terraform -chdir=infra/terraform init -reconfigure -backend-config=backend.hcl
terraform -chdir=infra/terraform fmt -check -recursive
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform plan -out=foundation.tfplan
terraform -chdir=infra/terraform apply foundation.tfplan
```

This enables APIs and creates five service accounts, least-privilege IAM,
Artifact Registry, the private/versioned ML bucket, one empty Secret Manager
secret, and five Cloud Tasks queues. It does not create services that would
reference missing images or missing secret versions.

## 3. Populate Secret Manager

Terraform creates the `stock-analysis-env` secret container but never stores its
payload in state. One JSON bundle stays below Secret Manager's six active-version
Always Free allowance. Use a protected file and never commit it or print it in logs.

The bundle accepts only string values for these keys:

```json
{
  "DJANGO_SECRET_KEY": "...",
  "DATABASE_URL": "postgresql://...?sslmode=require",
  "LANGGRAPH_DATABASE_URL": "postgresql://...?sslmode=require",
  "REDIS_URL": "rediss://...",
  "GOOGLE_API_KEY": "...",
  "FINNHUB_API_KEY": "...",
  "FRED_API_KEY": "...",
  "ALPHA_VANTAGE_API_KEY": "...",
  "NEWS_API_KEY": "...",
  "TAVILY_API_KEY": "..."
}
```

Example with a protected file:

```powershell
gcloud secrets versions add stock-analysis-env --data-file="C:\secure\stock-analysis-env.json"
```

Verify metadata only; never print payloads in CI logs:

```powershell
gcloud secrets versions list stock-analysis-env
```

## 4. Upload model artifacts

The bucket layout must match the names resolved by `ml/model_loader.py`:

```text
gs://PROJECT_ID-ml-models/
  finbert/                 # Hugging Face model/tokenizer directory
  regime_classifier/
    regime.joblib
```

```powershell
gcloud storage cp --recursive backend/ml_models/finbert "gs://$ProjectId-ml-models/finbert"
gcloud storage cp --recursive backend/ml_models/regime_classifier "gs://$ProjectId-ml-models/regime_classifier"
```

The worker downloads missing artifacts to `/tmp/stockanalysis-ml-models` on a
cold start. GCS remains private and the Cloud Run service account has read-only
object access.

## 5. Bootstrap the first images

The bootstrap build derives the stable backend Cloud Run URL from the project
number, builds both images, and pushes the `bootstrap` tag without deploying:

```powershell
gcloud builds submit --config=cloudbuild-bootstrap.yaml `
  --service-account="projects/$ProjectId/serviceAccounts/cloud-build-sa@$ProjectId.iam.gserviceaccount.com" `
  --substitutions="_GCP_REGION=us-central1,_IMAGE_TAG=bootstrap"
```

If the caller cannot act as `cloud-build-sa`, grant only
`roles/iam.serviceAccountUser` on that service account to the release operator.

## 6. Create the runtime resources

Set these values in `terraform.tfvars`:

```hcl
image_tag               = "bootstrap"
create_runtime_services = true
```

Then review and apply:

```powershell
terraform -chdir=infra/terraform plan -out=runtime.tfplan
terraform -chdir=infra/terraform apply runtime.tfplan
terraform -chdir=infra/terraform output
```

Terraform creates:

- public `frontend` and `backend-api` services with zero minimum instances;
- private/internal `task-worker` with one-request concurrency and 1 GiB memory;
- the `db-migrate` Cloud Run job;
- exactly three consolidated Scheduler jobs;
- service-specific Cloud Run Invoker bindings;
- an uptime check, two alert policies, and an operations dashboard.

Run the initial migration after creation:

```powershell
gcloud run jobs execute db-migrate --region=us-central1 --wait
```

## 7. Configure Cloud Build triggers

Connect the GitHub repository in Cloud Build, then create two triggers with
separate identities:

```text
PR CI: projects/PROJECT_ID/serviceAccounts/cloud-build-ci-sa@PROJECT_ID.iam.gserviceaccount.com
Deploy: projects/PROJECT_ID/serviceAccounts/cloud-build-sa@PROJECT_ID.iam.gserviceaccount.com
```

- Pull requests targeting `main`: `cloudbuild-ci.yaml`
- Pushes to `main`: `cloudbuild-deploy.yaml`

Set `_GCP_REGION=us-central1` and `_AR_REPO=stock-analysis`. Enable comment
control for untrusted external pull requests and require a successful PR trigger
check in branch protection. The deploy build pushes immutable
`${SHORT_SHA}` tags plus `latest`, updates and executes the migration job,
deploys all three services, and performs backend/frontend smoke checks.

## 8. Validate end to end

```powershell
$BackendUrl = terraform -chdir=infra/terraform output -raw backend_url
$FrontendUrl = terraform -chdir=infra/terraform output -raw frontend_url
Invoke-RestMethod "$BackendUrl/api/v1/health/live/"
Invoke-RestMethod "$BackendUrl/api/v1/health/ready/"
Invoke-WebRequest $FrontendUrl -UseBasicParsing
gcloud tasks queues list --location=us-central1
gcloud scheduler jobs list --location=us-central1
```

Then perform one authenticated analysis request, watch the `orchestrator` queue,
confirm a worker request in Cloud Logging, complete the PM review, and verify the
analysis reaches its terminal state. Scheduler jobs can be tested manually:

```powershell
gcloud scheduler jobs run market-data-hourly --location=us-central1
```

## Local-development compatibility

No local workflow needs Google credentials. `TASK_BACKEND` defaults to `celery`,
development settings permit internal requests only for local debugging, and
Docker Compose explicitly selects Celery. Run the existing quick-start commands
in the root README.

## Free-tier guardrails

- All Cloud Run services have zero minimum instances and CPU idling enabled.
- The backend/worker use 512 MiB/1 GiB respectively; concurrency is 40/1.
- Only three Scheduler jobs exist.
- Queue rates and concurrency cap fan-out and third-party API pressure.
- Artifact Registry deletes versions older than seven days while keeping three.
- Cloud Build uses the default free-eligible machine by omitting a machine override.
- One bundled secret version leaves five Always Free active-version slots for rotation.
- Model storage is one regional Standard bucket and should remain below 5 GB.
- Keep Redis connections below 30; Cloud Run worker concurrency is intentionally 1.

Review Billing reports, Cloud Run request/CPU/GiB-second usage, Cloud Build
minutes, Artifact Registry bytes, Cloud Tasks operations, GCS bytes/operations,
and external Neon/Redis dashboards every week.
