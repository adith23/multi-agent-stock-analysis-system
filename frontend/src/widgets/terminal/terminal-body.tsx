"use client";

import { type ReactNode, useState } from "react";
import { PanelLeft, PanelRight, X } from "lucide-react";

import { AuditTrailPanel } from "@/features/audit-trail/components/audit-trail-panel";
import { BullBearPanel } from "@/features/bull-bear/components/bull-bear-panel";
import { ICMemoPanel } from "@/features/ic-memo/components/ic-memo-panel";
import { RiskCompliancePanel } from "@/features/risk-compliance/components/risk-compliance-panel";
import { SpecialistReportsPanel } from "@/features/specialist-reports/components/specialist-reports-panel";
import { AnalyticsPanel } from "@/features/visualization/components/analytics-panel";
import { useKeyboardShortcut, useMediaQuery } from "@/shared/hooks";
import { cn } from "@/shared/lib";
import { FeatureErrorBoundary } from "@/shared/ui";
import { useTerminalStore } from "@/stores/terminal-store";

import { TabNavigation } from "./tab-navigation";

export function TerminalBody({ leftSidebar, rightSidebar }: { leftSidebar: ReactNode; rightSidebar: ReactNode }) {
  const activeTab = useTerminalStore((state) => state.activeTab);
  const compactLayout = useMediaQuery("(max-width: 1279px)");
  const [leftToggled, setLeftToggled] = useState(false);
  const [rightToggled, setRightToggled] = useState(false);
  const leftVisible = compactLayout ? leftToggled : !leftToggled;
  const rightVisible = compactLayout ? rightToggled : !rightToggled;

  useKeyboardShortcut("Escape", () => {
    setLeftToggled(false);
    setRightToggled(false);
  }, { enabled: compactLayout && (leftVisible || rightVisible) });

  function toggleLeftSidebar() {
    setLeftToggled((visible) => !visible);
    if (compactLayout) setRightToggled(false);
  }

  function toggleRightSidebar() {
    setRightToggled((visible) => !visible);
    if (compactLayout) setLeftToggled(false);
  }

  return (
    <div className="relative flex min-h-0 flex-1">
      {compactLayout && (leftVisible || rightVisible) ? (
        <button className="absolute inset-0 z-20 bg-void/75" type="button" aria-label="Close open sidebar" onClick={() => { setLeftToggled(false); setRightToggled(false); }} />
      ) : null}
      <div id="agent-pipeline-sidebar" className={cn("z-30 min-h-0 shrink-0", compactLayout && "absolute inset-y-0 left-0 shadow-2xl", !leftVisible && "hidden")}>
        {leftSidebar}
      </div>
      <section className="flex min-w-0 flex-1 flex-col bg-void" aria-label="Terminal workspace">
        <div className="relative shrink-0">
          <TabNavigation />
          <button
            type="button"
            className="absolute top-1 left-1 z-40 grid size-7 place-items-center border border-hairline bg-inset text-text-faint transition-colors hover:text-text-primary focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-amber"
            aria-controls="agent-pipeline-sidebar"
            aria-expanded={leftVisible}
            aria-label={leftVisible ? "Collapse agent pipeline" : "Expand agent pipeline"}
            onClick={toggleLeftSidebar}
          >
            {compactLayout && leftVisible ? <X className="size-3.5" aria-hidden="true" /> : <PanelLeft className="size-3.5" aria-hidden="true" />}
          </button>
          <button
            type="button"
            className="absolute top-1 right-1 z-40 grid size-7 place-items-center border border-hairline bg-inset text-text-faint transition-colors hover:text-text-primary focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-amber"
            aria-controls="portfolio-context-sidebar"
            aria-expanded={rightVisible}
            aria-label={rightVisible ? "Collapse portfolio context" : "Expand portfolio context"}
            onClick={toggleRightSidebar}
          >
            {compactLayout && rightVisible ? <X className="size-3.5" aria-hidden="true" /> : <PanelRight className="size-3.5" aria-hidden="true" />}
          </button>
        </div>
        <div
          id={`terminal-panel-${activeTab}`}
          role="tabpanel"
          aria-labelledby={`terminal-tab-${activeTab}`}
          className="terminal-workspace-grid min-h-0 flex-1 overflow-y-auto p-4"
        >
          <h1 className="sr-only">{activeTab} workspace</h1>
          <FeatureErrorBoundary resetKey={activeTab}>
            {activeTab === "overview" ? <ICMemoPanel /> : null}
            {activeTab === "specialists" ? <SpecialistReportsPanel /> : null}
            {activeTab === "adversarial" ? <BullBearPanel /> : null}
            {activeTab === "risk" ? <RiskCompliancePanel /> : null}
            {activeTab === "analytics" ? <AnalyticsPanel /> : null}
            {activeTab === "audit" ? <AuditTrailPanel /> : null}
          </FeatureErrorBoundary>
        </div>
      </section>
      <div id="portfolio-context-sidebar" className={cn("z-30 min-h-0 shrink-0", compactLayout && "absolute inset-y-0 right-0 shadow-2xl", !rightVisible && "hidden")}>
        {rightSidebar}
      </div>
    </div>
  );
}
