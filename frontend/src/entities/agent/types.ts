import type { JsonObject, JsonValue, VersionedApiEntity } from "@/shared/types";

export enum AgentStance {
  BULLISH = "bullish",
  BEARISH = "bearish",
  NEUTRAL = "neutral",
}

export const SPECIALIST_TYPES = ["macro", "fundamental", "technical", "sentiment"] as const;
export type SpecialistType = (typeof SPECIALIST_TYPES)[number];

export interface SpecialistReport {
  id: string;
  specialist: SpecialistType | string;
  thesis: string;
  summary: string;
  evidence: JsonValue[];
  assumptions: JsonValue[];
  limitations: JsonValue[];
  confidence: number;
  stance: AgentStance | "";
  generated_at: string;
  agent_version: string;
  model_version: string;
  prompt_version: string;
  version: number;
}

export interface BullBearDecisionMemo extends VersionedApiEntity {
  bull_case: string;
  bear_case: string;
  base_case: string;
  key_disagreements: JsonValue[];
  falsifiers: JsonValue[];
  evidence: JsonValue[];
  confidence: number;
  weak_assumptions: JsonValue[];
  missing_evidence: JsonValue[];
  material_unknowns: JsonValue[];
  premortem: JsonValue[];
  debate_rounds: number;
  output_snapshot: JsonObject;
}
