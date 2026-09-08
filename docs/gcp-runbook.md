# GCP operations and incident runbook

## Routine checks

Daily, inspect failed Cloud Build executions, Cloud Run 5xx logs, Cloud Tasks
retry counts, Scheduler results, database storage, and Redis memory/connections.
Weekly, inspect Artifact Registry storage and GCP Billing reports. Monthly,
reconcile actual usage with every provider's current free-tier limits.

Useful commands:

```powershell
gcloud run services list --region=us-central1
gcloud run jobs executions list --job=db-migrate --region=us-central1
gcloud tasks queues describe orchestrator --location=us-central1
gcloud scheduler jobs list --location=us-central1
gcloud builds list --limit=20
gcloud logging read 'resource.type="cloud_run_revision" severity>=ERROR' --limit=50
```

## Failed deployment

1. Stop; do not promote `latest` manually.
2. Read the first failing Cloud Build step and the migration execution logs.
3. If the migration failed, determine whether it is transactional and backward
   compatible before any service rollback.
4. Fix forward when a schema change has already committed. Roll back only when
   the previous revision is compatible with the current database schema.
5. Re-run the deploy trigger with a new immutable commit.

## Application rollback

List revisions and route all traffic to the last known-good revision:

```powershell
gcloud run revisions list --service=backend-api --region=us-central1
gcloud run services update-traffic backend-api --region=us-central1 --to-revisions=REVISION=100
gcloud run services update-traffic task-worker --region=us-central1 --to-revisions=REVISION=100
gcloud run services update-traffic frontend --region=us-central1 --to-revisions=REVISION=100
```

Rollback order is frontend, backend, then worker when an API contract regressed;
worker and backend must always use compatible task payload contracts. Record the
commit, image digest, revision, operator, reason, and validation result.

To make Terraform's declared state match the rollback, set `image_tag` to the
known-good immutable Git SHA, plan, and apply. Never use `terraform state rm` as
an incident shortcut.

## Queue incident

Pause a queue before investigating poison payloads or downstream failure:

```powershell
gcloud tasks queues pause orchestrator --location=us-central1
gcloud tasks queues describe orchestrator --location=us-central1
gcloud tasks queues resume orchestrator --location=us-central1
```

Do not purge by default; purge is destructive and prevents recovery. The worker
returns 5xx for execution failures so Cloud Tasks retries, 429 for an execution
already in progress, and 2xx for a completed replay.

## Scheduler incident

Pause only the affected job. Keep the other consolidated jobs running:

```powershell
gcloud scheduler jobs pause portfolio-monitors --location=us-central1
gcloud scheduler jobs resume portfolio-monitors --location=us-central1
```

## Secret rotation

1. Generate or rotate the credential at its source provider.
2. Add a new Secret Manager version; never overwrite Terraform state.
3. Deploy new Cloud Run revisions so instances resolve `latest` immediately.
4. Validate readiness and one representative operation.
5. Disable the prior version only after all old revisions stop receiving traffic.
6. Destroy the old version after the organization's recovery window.

Rotating `DJANGO_SECRET_KEY` invalidates signed Django sessions and tokens that
depend on it. Schedule that rotation and notify users.

Credentials share the `stock-analysis-env` bundle, so every rotation uploads a
complete validated JSON document. Keep no more than six enabled or disabled
versions across the billing account; destroyed versions do not count.

## Database recovery

Neon owns backups/PITR according to the selected plan. Before destructive schema
work, verify the actual plan's recovery window. Migrations must be backward
compatible: expand schema, deploy readers/writers, backfill, then contract in a
later deployment. Never couple irreversible data deletion to a normal release.

## Load validation within guardrails

Use the existing Locust suite from a controlled client, beginning well below the
free-tier envelope:

```powershell
backend/venv/Scripts/python.exe -m locust -f backend/tests/load/locustfile.py `
  --host=$BackendUrl --headless --users=5 --spawn-rate=1 --run-time=5m
```

Increase one variable at a time while watching P95 latency, instance count,
memory, queue depth, Neon connections, and Redis connections. Stop before 30
Redis connections, persistent queue growth, repeated 429/5xx responses, or a
projected monthly Cloud Run usage above the current free allowance. Do not run
an unbounded or public load test.

## Security audit checklist

- Worker has no `allUsers`/`allAuthenticatedUsers` invoker binding.
- Only `cloud-tasks-sa` invokes the worker and only `cloud-scheduler-sa` invokes
  scheduler routes.
- Cloud Run runtime identity has secret read, task enqueue, and model object-read
  access—no editor/owner role.
- PR validation uses `cloud-build-ci-sa` without deploy permissions; main-branch
  delivery uses `cloud-build-sa`. There are no downloaded service-account keys.
- Secret payloads do not appear in Terraform state, build arguments, logs, or Git.
- GCS public access prevention and uniform bucket-level access remain enabled.
- Backend CORS contains only the deployed frontend origin.
- IAM changes are reviewed through Terraform plans.
