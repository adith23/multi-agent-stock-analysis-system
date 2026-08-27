import type { AgentStance } from "@/entities/agent";
import type { ActionSignal, RecommendationStatus } from "@/entities/recommendation";

export interface CatalystView { name: string; date: string; probability: number; }
export interface ReturnRangeView { bear: number; base: number; bull: number; }
export interface SignalAgreementView { agent: string; stance: AgentStance; }
export interface ICMemoView {
  ticker: string; company: string; action: ActionSignal; conviction: number; status: RecommendationStatus;
  thesis: string; timeHorizon: string; horizonDriver: string; catalyst: CatalystView;
  expectedReturn: ReturnRangeView; positionSizing: string; agreement: readonly SignalAgreementView[];
  keyRisk: string; invalidation: string; reviewVersion: number | null;
}
