"use client";

import { useRef } from "react";
import { WifiOff } from "lucide-react";

import { AgentPipelineSidebar } from "@/features/analysis-pipeline/components/agent-pipeline-sidebar";
import { useAnalysisSynchronization } from "@/features/analysis-pipeline/hooks/use-analysis-synchronization";
import { usePipelineStream } from "@/features/analysis-pipeline/hooks/use-pipeline-stream";
import { useRunAnalysis } from "@/features/analysis-pipeline/hooks/use-run-analysis";
import { useAlertStream } from "@/features/alert-stream";
import { PortfolioContextSidebar } from "@/features/portfolio-context/components/portfolio-context-sidebar";
import { TickerStrip } from "@/features/ticker-search/components/ticker-strip";
import { useOnlineStatus } from "@/shared/hooks";
import { useTerminalStore } from "@/stores/terminal-store";

import { StatusTicker } from "./status-ticker";
import { TerminalBody } from "./terminal-body";
import { TerminalHeader } from "./terminal-header";
import { useTerminalKeyboardShortcuts } from "./use-terminal-keyboard-shortcuts";

export function ConclaveTerminal() {
  const tickerInputRef = useRef<HTMLInputElement>(null);
  const isOnline = useOnlineStatus();
  useTerminalKeyboardShortcuts(tickerInputRef);
  const runAnalysis = useRunAnalysis();
  const activeRunId = useTerminalStore((state) => state.activeRunId);
  useAnalysisSynchronization(activeRunId);
  const pipelineStream = usePipelineStream(activeRunId);
  const alertStream = useAlertStream();

  return (
    <main className="flex h-dvh min-w-[1080px] flex-col overflow-hidden bg-void text-text-primary">
      <TerminalHeader
        tickerInputRef={tickerInputRef}
        onTickerSubmit={(symbol) => runAnalysis.mutate({ symbol })}
        isSubmitting={runAnalysis.isPending}
        pipelineStreamStatus={pipelineStream.status}
        alertStreamStatus={alertStream.status}
      />
      {!isOnline ? (
        <div className="flex min-h-8 items-center justify-center gap-2 border-b border-amber/35 bg-amber/10 px-3 font-mono text-[10px] text-amber" role="status" aria-live="polite">
          <WifiOff className="size-3.5" aria-hidden="true" />Offline — live analysis and data refresh are paused.
        </div>
      ) : null}
      <TickerStrip />
      <TerminalBody leftSidebar={<AgentPipelineSidebar />} rightSidebar={<PortfolioContextSidebar />} />
      <StatusTicker />
    </main>
  );
}
