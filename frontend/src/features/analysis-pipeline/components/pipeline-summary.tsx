import { useMemo } from "react";

import { usePipelineStore } from "@/stores/pipeline-store";

import { PIPELINE_STAGES } from "../model/pipeline-stages";

export function PipelineSummary() {
  const stages = usePipelineStore((state) => state.stages);
  const completedCount = useMemo(
    () => PIPELINE_STAGES.filter((stage) => stages[stage.id] === "done").length,
    [stages],
  );

  return (
    <div className="border-t border-hairline bg-inset/45 px-3 py-2.5">
      <div className="flex items-center justify-between font-mono text-[9px] tracking-[0.06em] text-text-faint uppercase">
        <span>Pipeline summary</span>
        <span aria-live="polite">{completedCount}/{PIPELINE_STAGES.length} complete</span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-1.5 text-center font-mono">
        <div className="border border-hairline bg-void/45 px-1.5 py-1">
          <strong className="block text-[11px] text-text-primary">14</strong>
          <span className="text-[8px] tracking-wide text-text-faint uppercase">Mock sources</span>
        </div>
        <div className="border border-hairline bg-void/45 px-1.5 py-1">
          <strong className="block text-[11px] text-text-primary">1,204</strong>
          <span className="text-[8px] tracking-wide text-text-faint uppercase">Records</span>
        </div>
      </div>
    </div>
  );
}
