import type { JsonObject, JsonValue, VersionedApiEntity } from "@/shared/types";

export enum RiskDecision {
  PASS = "pass",
  PASS_WITH_WARNINGS = "pass_with_warnings",
  REDUCE_SIZE = "reduce_size",
  HEDGE_REQUIRED = "hedge_required",
  BLOCK = "block",
  ESCALATE = "escalate",
}

export enum ComplianceDecision {
  APPROVED = "approved",
  RESTRICTED = "restricted",
  REQUIRES_APPROVAL = "requires_approval",
  VIOLATED = "violated",
  ESCALATED = "escalated",
}

export interface RiskValidation extends VersionedApiEntity {
  decision: RiskDecision;
  passed: boolean;
  risk_metrics: JsonObject;
  breaches: JsonValue[];
  mitigations: JsonValue[];
  hedge_suggestions: JsonValue[];
  scenario_results: JsonObject;
  rationale: string;
  requires_escalation: boolean;
  rule_version: string;
}

export interface ComplianceResult extends VersionedApiEntity {
  decision: ComplianceDecision;
  passed: boolean;
  restricted_list_match: boolean;
  checks: JsonValue[];
  violations: JsonValue[];
  approval_required: boolean;
  overridden: boolean;
  reviewer: string | null;
  review_rationale: string;
  reviewed_at: string | null;
  rule_version: string;
}

export interface RiskComplianceResponse {
  risk: RiskValidation;
  compliance: ComplianceResult;
  approval_gate: JsonObject;
}
