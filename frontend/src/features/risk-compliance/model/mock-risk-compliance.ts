import type { RiskComplianceView } from "../types/risk-compliance.types";

export const MOCK_RISK_COMPLIANCE: Readonly<RiskComplianceView> = {
  status: "PASS WITH CONDITIONS",
  exposures: [{ label: "Concentration", value: 62, limit: 80 }, { label: "Leverage", value: 34, limit: 100 }, { label: "Liquidity (days to exit)", value: 48, limit: 100 }, { label: "Factor correlation", value: 71, limit: 80 }],
  stressTests: [{ scenario: "Rates +100 bps", impact: "-1.8% portfolio NAV" }, { scenario: "AI capex growth -30%", impact: "-3.1% position-level" }, { scenario: "Sector rotation to value", impact: "-0.9% portfolio NAV" }],
  note: "Concentration and correlation exposure are elevated but within hard limits. Recommend phased entry to avoid single-day liquidity impact.",
  restrictedListStatus: "CLEAR", checks: [{ label: "Restricted list screen", pass: true }, { label: "Insider window check", pass: true }, { label: "Mandate / style-box fit", pass: true }, { label: "Concentration policy (single name ≤ 5% NAV)", pass: true }], escalation: "NONE",
};
