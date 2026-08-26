export interface ApiInfo {
  name: string;
  version: string;
  status: string;
}

export interface Liveness {
  status: string;
}

export interface ReadinessChecks {
  database: boolean;
  cache: boolean;
  celery_broker: boolean;
}

export interface Readiness {
  status: string;
  checks: ReadinessChecks;
}
