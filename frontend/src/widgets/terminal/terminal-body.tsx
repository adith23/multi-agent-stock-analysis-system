import type { ReactNode } from "react";

import { AuditTrailPanel } from "@/features/audit-trail/components/audit-trail-panel";
import { BullBearPanel } from "@/features/bull-bear/components/bull-bear-panel";
import { ICMemoPanel } from "@/features/ic-memo/components/ic-memo-panel";
import { RiskCompliancePanel } from "@/features/risk-compliance/components/risk-compliance-panel";
import { SpecialistReportsPanel } from "@/features/specialist-reports/components/specialist-reports-panel";
import { AnalyticsPanel } from "@/features/visualization/components/analytics-panel";
import { useTerminalStore } from "@/stores/terminal-store";

import { TabNavigation } from "./tab-navigation";

export function TerminalBody({ leftSidebar, rightSidebar }: { leftSidebar: ReactNode; rightSidebar: ReactNode }) {
  const activeTab = useTerminalStore((state) => state.activeTab);

  return (
    <div className="flex min-h-0 flex-1">
      {leftSidebar}
      <section className="flex min-w-0 flex-1 flex-col bg-void" aria-label="Terminal workspace">
        <TabNavigation />
        <div
          id={`terminal-panel-${activeTab}`}
          role="tabpanel"
          aria-labelledby={`terminal-tab-${activeTab}`}
          className="terminal-workspace-grid min-h-0 flex-1 overflow-y-auto p-4"
        >
          <h1 className="sr-only">{activeTab} workspace</h1>
          {activeTab === "overview" ? <ICMemoPanel /> : null}
          {activeTab === "specialists" ? <SpecialistReportsPanel /> : null}
          {activeTab === "adversarial" ? <BullBearPanel /> : null}
          {activeTab === "risk" ? <RiskCompliancePanel /> : null}
          {activeTab === "analytics" ? <AnalyticsPanel /> : null}
          {activeTab === "audit" ? <AuditTrailPanel /> : null}
        </div>
      </section>
      {rightSidebar}
    </div>
  );
}
