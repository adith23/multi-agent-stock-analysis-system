import type { DecimalString, JsonObject, JsonValue, VersionedApiEntity } from "@/shared/types";

export enum ActionSignal {
  STRONG_BUY = "strong_buy",
  BUY = "buy",
  ACCUMULATE = "accumulate",
  HOLD = "hold",
  REDUCE = "reduce",
  SELL = "sell",
  STRONG_SELL = "strong_sell",
  NOT_BUY = "not_buy",
  NOT_SELL = "not_sell",
}

export enum TimeHorizon {
  TACTICAL = "tactical",
  MEDIUM_TERM = "medium_term",
  STRATEGIC = "strategic",
}

export enum RecommendationStatus {
  PENDING_REVIEW = "pending_review",
  APPROVED = "approved",
  REJECTED = "rejected",
  DEFERRED = "deferred",
}

export enum ReviewRequestStatus {
  PENDING = "pending",
  COMPLETED = "completed",
  EXPIRED = "expired",
  CANCELLED = "cancelled",
}

export type PMReviewDecision = "approve" | "reject" | "defer";

export interface ConvictionScorePackage extends VersionedApiEntity {
  score: number;
  level: string;
  action_signal: ActionSignal;
  expected_return_low: number | null;
  expected_return_high: number | null;
  horizon_days: number | null;
  component_scores: JsonObject;
  evidence: JsonValue[];
  caveats: JsonValue[];
}

export interface SignalAgreementMatrix extends VersionedApiEntity {
  signal_stances: JsonObject;
  agreements: JsonValue[];
  conflicts: JsonValue[];
  agreement_ratio: number;
}

export interface ConvictionResponse {
  score: ConvictionScorePackage;
  agreement: SignalAgreementMatrix;
}

export interface ReviewRequestSummary {
  id: string;
  status: ReviewRequestStatus;
  expires_at: string;
  version: number;
  decision: PMReviewDecision | null;
  decided_at: string | null;
}

export interface PositionSizing {
  methodology: string;
  portfolio_weight_pct: DecimalString;
  dollar_amount: DecimalString;
  num_shares: number;
  assumptions: JsonObject;
}

export interface ExitStrategy {
  status: "pending" | "active" | "triggered" | "closed";
  stop_loss_price: DecimalString;
  profit_targets: JsonValue[];
  thesis_invalidation_triggers: JsonValue[];
  time_based_review_date: string;
}

export interface PMRecommendation extends VersionedApiEntity {
  action: ActionSignal;
  conviction: number;
  status: RecommendationStatus;
  summary: string;
  rationale: string;
  expected_return: JsonObject;
  position_size: JsonObject;
  entry_plan: JsonValue[];
  exit_conditions: JsonObject;
  time_horizon: TimeHorizon;
  catalysts: JsonValue[];
  portfolio_fit: string;
  capital_allocation_guidance: string;
  conditions_precedent: JsonValue[];
  evidence: JsonValue[];
  assumptions: JsonValue[];
  limitations: JsonValue[];
  reviewer: string | null;
  review_rationale: string;
  reviewed_at: string | null;
  review_request: ReviewRequestSummary | null;
  position_sizing: PositionSizing | null;
  exit_strategy: ExitStrategy | null;
}

export interface PMReviewRequest {
  decision: PMReviewDecision;
  rationale: string;
  expected_version: number;
}

export interface PMReviewResponse {
  analysis_run_id: string;
  decision: PMReviewDecision;
  status: "review_accepted" | "review_replayed";
  review_version: number;
}
