import type { ApiEntity, JsonObject, JsonValue } from "@/shared/types";

export enum PipelineStatus {
  PENDING = "pending",
  INGESTING = "ingesting",
  EXTRACTING_SIGNALS = "extracting_signals",
  RUNNING_SPECIALISTS = "running_specialists",
  PEER_ANALYSIS = "peer_analysis",
  ADVERSARIAL_REVIEW = "adversarial_review",
  CONVICTION_SCORING = "conviction_scoring",
  RISK_VALIDATION = "risk_validation",
  COMPLIANCE_CHECK = "compliance_check",
  POSITION_SIZING = "position_sizing",
  PORTFOLIO_OPTIMIZATION = "portfolio_optimization",
  PM_SYNTHESIS = "pm_synthesis",
  AWAITING_PM_APPROVAL = "awaiting_pm_approval",
  BLOCKED = "blocked",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export enum AnalysisScope {
  SINGLE = "single",
  WATCHLIST = "watchlist",
  SECTOR = "sector",
  UNIVERSE = "universe",
}

export enum PipelineStepStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  SKIPPED = "skipped",
}

export interface PipelineStepResult {
  id: string;
  step_name: string;
  sequence: number;
  status: PipelineStepStatus;
  attempt: number;
  warnings: JsonValue[];
  error_message: string;
  duration_ms: number | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface AnalysisRun extends ApiEntity {
  symbol: string;
  exchange: string;
  scope: AnalysisScope;
  status: PipelineStatus;
  current_stage: string;
  initiated_by: string | null;
  celery_task_id: string;
  data_cutoff_at: string;
  configuration_hash: string;
  manifest_hash: string;
  error_message: string;
  started_at: string | null;
  completed_at: string | null;
  steps: PipelineStepResult[];
}

export interface AnalysisCreateRequest {
  symbol: string;
  exchange?: string;
  scope?: AnalysisScope.SINGLE;
  config?: JsonObject;
  as_of?: string;
}

export interface AnalysisCreateHeaders {
  "Idempotency-Key": string;
}
