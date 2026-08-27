import { AgentStance } from "@/entities/agent";
import type { ConvictionResponse, PMRecommendation } from "@/entities/recommendation";
import type { JsonObject, JsonValue } from "@/shared/types";
import type { ICMemoView, SignalAgreementView } from "../types/ic-memo.types";

const text = (value: JsonValue | undefined, fallback: string) => typeof value === "string" && value.trim() ? value : fallback;
const number = (value: JsonValue | undefined, fallback: number) => typeof value === "number" && Number.isFinite(value) ? value : fallback;
const record = (value: JsonValue | undefined): JsonObject => value && typeof value === "object" && !Array.isArray(value) ? value : {};

function agreementViews(conviction?: ConvictionResponse): SignalAgreementView[] {
  return Object.entries(conviction?.agreement.signal_stances ?? {}).flatMap(([agent, value]) =>
    value === AgentStance.BULLISH || value === AgentStance.BEARISH || value === AgentStance.NEUTRAL ? [{ agent, stance: value }] : [],
  );
}

export function toICMemoView(recommendation: PMRecommendation, ticker: string, conviction?: ConvictionResponse): ICMemoView {
  const returns = recommendation.expected_return;
  const firstCatalyst = record(recommendation.catalysts[0]);
  const sizing = recommendation.position_sizing;
  return {
    ticker, company: "Backend recommendation", action: recommendation.action, conviction: recommendation.conviction,
    status: recommendation.status, thesis: recommendation.summary || recommendation.rationale,
    timeHorizon: recommendation.time_horizon.replaceAll("_", " "),
    horizonDriver: recommendation.capital_allocation_guidance || recommendation.portfolio_fit,
    catalyst: { name: text(firstCatalyst.title ?? firstCatalyst.name, "See recommendation catalysts"), date: text(firstCatalyst.expected_at ?? firstCatalyst.date, "Date not supplied"), probability: number(firstCatalyst.probability, 0) },
    expectedReturn: { bear: number(returns.bear ?? returns.low, 0), base: number(returns.base ?? returns.mid, 0), bull: number(returns.bull ?? returns.high, 0) },
    positionSizing: sizing ? `${sizing.portfolio_weight_pct}% NAV · ${sizing.methodology} · ${sizing.num_shares} shares` : "Sizing package not available",
    agreement: agreementViews(conviction),
    keyRisk: text(recommendation.limitations[0], "See risk and compliance tab for the validated risk package."),
    invalidation: recommendation.exit_strategy ? text(recommendation.exit_strategy.thesis_invalidation_triggers[0], "See exit strategy package") : "Exit strategy not available",
    reviewVersion: recommendation.review_request?.version ?? null,
  };
}
