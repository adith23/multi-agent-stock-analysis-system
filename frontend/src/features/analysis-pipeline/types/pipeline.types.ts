import type { LucideIcon } from "lucide-react";

import type { ActiveSpecialist, TerminalTab } from "@/stores/terminal-store";

export type PipelineLayerId = "data" | "analysis" | "synthesis" | "decision";

export interface PipelineNavigationTarget {
  tab: TerminalTab;
  specialist?: ActiveSpecialist;
}

export interface PipelineStageDefinition {
  id: string;
  layer: PipelineLayerId;
  name: string;
  agent: string;
  requirement: string;
  icon: LucideIcon;
  navigation: PipelineNavigationTarget;
  backendStatuses: readonly string[];
}

export interface PipelineLayerDefinition {
  id: PipelineLayerId;
  label: string;
}
