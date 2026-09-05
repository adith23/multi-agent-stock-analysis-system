import type { BullBearMemoView } from "../types/bull-bear.types";

export const MOCK_BULL_BEAR: Readonly<BullBearMemoView> = {
  bullArguments: ["Data-center accelerator demand outstrips supply through FY27", "Gross-margin trajectory supports multiple expansion", "Net cash provides buyback and acquisition optionality"],
  bearArguments: ["Customer concentration is understated in consensus models", "Export licensing changes could delay shipments", "Valuation already prices in high-20s revenue growth"],
  weakAssumptions: ["Backlog-to-revenue conversion is assumed flat versus the prior cycle", "Tariff exposure is modeled as static with no escalation scenario"],
  preMortem: ["Q3 data-center revenue growth prints below 22% YoY", "The two largest customers signal dual-sourcing"],
  materialUnknowns: ["Next-gen node yield rates", "Competitor capacity ramp timeline"], roundsCompleted: 3,
};
