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

export interface RegimeChangeEventData {
  regime: string;
  previous: string;
  detected_at: string;
}

export interface ExitTriggerEventData {
  ticker: string;
  trigger: string;
  price: number;
  detected_at?: string;
}

export type AlertSseEventType = "regime_change" | "exit_trigger";
