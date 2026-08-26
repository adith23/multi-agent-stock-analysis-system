import type { DecimalString, JsonObject, JsonValue } from "@/shared/types";

export interface PortfolioState {
  id: string;
  portfolio_code: string;
  name: string;
  owner: string | null;
  as_of: string;
  base_currency: string;
  total_value: DecimalString;
  holdings: JsonValue[];
  weights: JsonObject;
  sector_exposures: JsonObject;
  factor_exposures: JsonObject;
  liquidity_metrics: JsonObject;
  risk_metrics: JsonObject;
  gross_leverage: number;
  version: number;
  created_at: string;
}

export interface PortfolioRisk {
  portfolio_code: string;
  as_of: string;
  gross_leverage: number;
  sector_exposures: JsonObject;
  factor_exposures: JsonObject;
  liquidity_metrics: JsonObject;
  risk_metrics: JsonObject;
}

export interface ScenarioRequest {
  name: string;
  positions: Record<string, number>;
  factor_exposures: JsonObject;
  factor_shocks: Record<string, number>;
  asset_shocks?: Record<string, number>;
  portfolio_code?: string;
  analysis_run_id?: string;
}

export interface ScenarioResult {
  id: string;
  name: string;
  scenario_type: string;
  inputs: JsonObject;
  results: JsonObject;
  worst_impact: number | null;
  initiated_by: string | null;
  created_at: string;
}

export interface PerformanceAttribution {
  id: string;
  symbol: string;
  action: string;
  measurement_period: string;
  period_start: string;
  period_end: string;
  entry_price: DecimalString;
  exit_price: DecimalString;
  realized_return: number;
  benchmark_return: number;
  excess_return: number;
  hit: boolean;
  risk_adjusted_return: number | null;
  agent_attribution: JsonObject;
  signal_decay: JsonObject;
  version: number;
}

export interface PerformanceResponse {
  summary: JsonObject;
  records: PerformanceAttribution[];
}

export type CatalystDirection = "positive" | "negative" | "uncertain";
export type CatalystOutcomeStatus = "pending" | "occurred" | "failed" | "delayed" | "cancelled";

export interface Catalyst {
  id: string;
  symbol: string;
  title: string;
  description: string;
  catalyst_type: string;
  expected_at: string | null;
  actual_at: string | null;
  direction: CatalystDirection;
  probability: number | null;
  impact: string;
  evidence: JsonValue[];
  is_active: boolean;
  is_thesis_critical: boolean;
  outcome_status: CatalystOutcomeStatus;
  outcome_notes: string;
  last_checked_at: string | null;
  version: number;
}

export type AlertType = "regime_transition" | "exit_trigger" | "catalyst_delayed";
export type AlertSeverity = "info" | "warning" | "critical";

export interface Alert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  detected_at: string;
  symbol: string | null;
  title: string;
  details: JsonObject;
}

/** Frontend projection used by the terminal health rail; no backend endpoint exists yet. */
export interface DataSourceHealth {
  name: string;
  status: "ok" | "delayed" | "down";
  last_sync: string;
}
