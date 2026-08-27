"use client";

import { AgentPipelineSidebar } from "@/features/analysis-pipeline/components/agent-pipeline-sidebar";
import { useAnalysisSynchronization } from "@/features/analysis-pipeline/hooks/use-analysis-synchronization";
import { usePipelineStream } from "@/features/analysis-pipeline/hooks/use-pipeline-stream";
import { useRunAnalysis } from "@/features/analysis-pipeline/hooks/use-run-analysis";
import { useAlertStream } from "@/features/alert-stream";
import { PortfolioContextSidebar } from "@/features/portfolio-context/components/portfolio-context-sidebar";
import { TickerStrip } from "@/features/ticker-search/components/ticker-strip";
import { useTerminalStore } from "@/stores/terminal-store";

import { StatusTicker } from "./status-ticker";
import { TerminalBody } from "./terminal-body";
import { TerminalHeader } from "./terminal-header";

export function ConclaveTerminal() {
  const runAnalysis = useRunAnalysis();
  const activeRunId = useTerminalStore((state) => state.activeRunId);
  useAnalysisSynchronization(activeRunId);
  const pipelineStream = usePipelineStream(activeRunId);
  const alertStream = useAlertStream();

  return (
    <main className="flex h-dvh min-w-[1080px] flex-col overflow-hidden bg-void text-text-primary">
      <TerminalHeader
        onTickerSubmit={(symbol) => runAnalysis.mutate({ symbol })}
        isSubmitting={runAnalysis.isPending}
        pipelineStreamStatus={pipelineStream.status}
        alertStreamStatus={alertStream.status}
      />
      <TickerStrip />
      <TerminalBody leftSidebar={<AgentPipelineSidebar />} rightSidebar={<PortfolioContextSidebar />} />
      <StatusTicker />
    </main>
  );
}
