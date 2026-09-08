terraform {
  # Supply bucket and prefix during init; backend blocks cannot use variables.
  # terraform init -backend-config="bucket=PROJECT-tf-state" \
  #   -backend-config="prefix=stock-analysis/production"
  backend "gcs" {}
}
