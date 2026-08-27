import { AgentStance } from "@/entities/agent";
import { ActionSignal, RecommendationStatus } from "@/entities/recommendation";
import type { ICMemoView } from "../types/ic-memo.types";

export const MOCK_IC_MEMO: Readonly<ICMemoView> = {
  ticker: "HLXD", company: "Helios Dynamics, Inc.", action: ActionSignal.BUY, conviction: 78,
  status: RecommendationStatus.PENDING_REVIEW,
  thesis: "Data-center compute demand and margin mix outweigh near-term tariff exposure. Initiate a standard-weight position ahead of the Q3 print; scale on confirmation of backlog conversion.",
  timeHorizon: "Medium-Term (1–6 mo)", horizonDriver: "Catalyst-driven — Q3 data-center revenue print",
  catalyst: { name: "Q3 Earnings", date: "Nov 20, 2026", probability: 68 },
  expectedReturn: { bear: -8, base: 19, bull: 34 },
  positionSizing: "2.4% NAV target, phased in 3 tranches over 5 sessions",
  agreement: [
    { agent: "Macro / Regime", stance: AgentStance.BULLISH }, { agent: "Fundamental", stance: AgentStance.BULLISH },
    { agent: "Technical", stance: AgentStance.NEUTRAL }, { agent: "Sentiment", stance: AgentStance.BULLISH },
  ],
  keyRisk: "Data-center revenue growth decelerates below 22% YoY",
  invalidation: "Two consecutive quarters of gross-margin compression greater than 150 bps", reviewVersion: 1,
};
