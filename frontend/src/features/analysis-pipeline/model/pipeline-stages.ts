import {
  BarChart3,
  Database,
  FileText,
  Gavel,
  Globe2,
  Newspaper,
  Scale,
  ShieldAlert,
  Swords,
} from "lucide-react";

import type { PipelineLayerDefinition, PipelineStageDefinition } from "../types/pipeline.types";

export const PIPELINE_LAYERS: readonly PipelineLayerDefinition[] = [
  { id: "data", label: "Data" },
  { id: "analysis", label: "Analysis" },
  { id: "synthesis", label: "Synthesis" },
  { id: "decision", label: "Decision" },
];

/**
 * UI stages aggregate the finer-grained AnalysisRun statuses currently emitted
 * by the backend task graph. Transport wiring is intentionally deferred.
 */
export const PIPELINE_STAGES: readonly PipelineStageDefinition[] = [
  {
    id: "data",
    layer: "data",
    name: "Data",
    agent: "Data Collector",
    requirement: "FR-001–007",
    icon: Database,
    navigation: { tab: "overview" },
    backendStatuses: ["INGESTING", "EXTRACTING_SIGNALS"],
  },
  {
    id: "macro",
    layer: "analysis",
    name: "Macro-Regime",
    agent: "Macro Analyst",
    requirement: "FR-008–013",
    icon: Globe2,
    navigation: { tab: "specialists", specialist: "macro" },
    backendStatuses: ["RUNNING_SPECIALISTS"],
  },
  {
    id: "fundamental",
    layer: "analysis",
    name: "Fundamental",
    agent: "Research Analyst",
    requirement: "FR-014–020",
    icon: FileText,
    navigation: { tab: "specialists", specialist: "fundamental" },
    backendStatuses: ["RUNNING_SPECIALISTS"],
  },
  {
    id: "technical",
    layer: "analysis",
    name: "Technical",
    agent: "Technical Analyst",
    requirement: "FR-021–026",
    icon: BarChart3,
    navigation: { tab: "specialists", specialist: "technical" },
    backendStatuses: ["RUNNING_SPECIALISTS"],
  },
  {
    id: "sentiment",
    layer: "analysis",
    name: "Sentiment & News",
    agent: "Sentiment Analyst",
    requirement: "FR-027–033",
    icon: Newspaper,
    navigation: { tab: "specialists", specialist: "sentiment" },
    backendStatuses: ["RUNNING_SPECIALISTS"],
  },
  {
    id: "bullbear",
    layer: "synthesis",
    name: "Bull vs. Bear",
    agent: "Adversarial Review",
    requirement: "FR-034–039",
    icon: Swords,
    navigation: { tab: "adversarial" },
    backendStatuses: ["PEER_ANALYSIS", "ADVERSARIAL_REVIEW", "CONVICTION_SCORING"],
  },
  {
    id: "risk",
    layer: "decision",
    name: "Risk Manager",
    agent: "Risk Agent",
    requirement: "FR-040–046",
    icon: ShieldAlert,
    navigation: { tab: "risk" },
    backendStatuses: ["RISK_VALIDATION"],
  },
  {
    id: "compliance",
    layer: "decision",
    name: "Compliance",
    agent: "Compliance Agent",
    requirement: "NFR-018–020",
    icon: Gavel,
    navigation: { tab: "risk" },
    backendStatuses: ["COMPLIANCE_CHECK", "BLOCKED"],
  },
  {
    id: "pm",
    layer: "decision",
    name: "Portfolio Manager",
    agent: "PM Synthesis",
    requirement: "FR-047–052",
    icon: Scale,
    navigation: { tab: "overview" },
    backendStatuses: [
      "POSITION_SIZING",
      "PORTFOLIO_OPTIMIZATION",
      "PM_SYNTHESIS",
      "AWAITING_PM_APPROVAL",
      "COMPLETED",
    ],
  },
];
