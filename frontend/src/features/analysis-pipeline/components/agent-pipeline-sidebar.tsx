import { Workflow } from "lucide-react";

import { cn } from "@/shared/lib";
import { SectionLabel } from "@/shared/ui";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useTerminalStore } from "@/stores/terminal-store";

import { PIPELINE_LAYERS, PIPELINE_STAGES } from "../model/pipeline-stages";
import type { PipelineStageDefinition } from "../types/pipeline.types";
import { PipelineStageIndicator } from "./pipeline-stage-indicator";
import { PipelineSummary } from "./pipeline-summary";

function PipelineStageButton({ stage }: { stage: PipelineStageDefinition }) {
  const status = usePipelineStore((state) => state.stages[stage.id] ?? "pending");
  const activeTab = useTerminalStore((state) => state.activeTab);
  const activeSpecialist = useTerminalStore((state) => state.activeSpecialist);
  const setActiveTab = useTerminalStore((state) => state.setActiveTab);
  const setActiveSpecialist = useTerminalStore((state) => state.setActiveSpecialist);
  const hasUniqueDestination = Boolean(stage.navigation.specialist) || stage.navigation.tab === "adversarial";
  const isActive = hasUniqueDestination && activeTab === stage.navigation.tab && (
    !stage.navigation.specialist || activeSpecialist === stage.navigation.specialist
  );
  const Icon = stage.icon;

  function navigateToStage() {
    if (stage.navigation.specialist) setActiveSpecialist(stage.navigation.specialist);
    setActiveTab(stage.navigation.tab);
  }

  return (
    <button
      type="button"
      className={cn(
        "group flex w-full items-center gap-2 border-l-2 px-2 py-1.5 text-left outline-none transition-colors hover:bg-panel-raised focus-visible:bg-panel-raised focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-amber/50",
        isActive ? "border-amber bg-amber/[0.055]" : "border-transparent",
      )}
      aria-current={isActive ? "page" : undefined}
      title={`Backend mapping: ${stage.backendStatuses.join(", ")}`}
      onClick={navigateToStage}
    >
      <PipelineStageIndicator status={status} stageName={stage.name} />
      <Icon className={cn("size-3.5 shrink-0", isActive ? "text-amber" : "text-text-faint group-hover:text-text-dim")} strokeWidth={1.6} aria-hidden="true" />
      <span className="min-w-0 flex-1">
        <span className={cn("block truncate font-mono text-[10px]", isActive ? "text-text-primary" : "text-text-dim")}>{stage.name}</span>
        <span className="block truncate text-[9px] text-text-faint">{stage.agent}</span>
      </span>
      <span className="font-mono text-[7px] text-text-faint">{stage.requirement}</span>
    </button>
  );
}

export function AgentPipelineSidebar() {
  return (
    <aside className="flex min-h-0 w-[226px] shrink-0 flex-col border-r border-hairline bg-panel" aria-label="Agent pipeline">
      <div className="px-3 pt-3">
        <SectionLabel icon={Workflow} className="mb-2">Agent pipeline</SectionLabel>
      </div>
      <nav className="min-h-0 flex-1 overflow-y-auto pb-2" aria-label="Pipeline stages">
        {PIPELINE_LAYERS.map((layer) => {
          const stages = PIPELINE_STAGES.filter((stage) => stage.layer === layer.id);
          return (
            <section key={layer.id} aria-labelledby={`pipeline-layer-${layer.id}`}>
              <h3 id={`pipeline-layer-${layer.id}`} className="border-y border-hairline bg-inset/55 px-3 py-1 font-mono text-[8px] font-medium tracking-[0.16em] text-text-faint uppercase">
                {layer.label}
              </h3>
              <div className="py-0.5">
                {stages.map((stage) => <PipelineStageButton key={stage.id} stage={stage} />)}
              </div>
            </section>
          );
        })}
      </nav>
      <PipelineSummary />
    </aside>
  );
}
