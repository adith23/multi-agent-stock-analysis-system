import { useState } from "react";
import { AlertTriangle, Calendar, Target, TrendingUp, XCircle } from "lucide-react";

import { AuditAction } from "@/entities/audit";
import { RecommendationStatus, type PMReviewDecision } from "@/entities/recommendation";
import { DataModeBadge, FeatureError, FeatureLoading, Panel, SectionLabel } from "@/shared/ui";
import { useAuditStore } from "@/stores/audit-store";
import { useTerminalStore } from "@/stores/terminal-store";

import { usePMDecision } from "../hooks/use-pm-decision";
import { useConviction, useRecommendation } from "../hooks/use-recommendation";
import { MOCK_IC_MEMO } from "../model/mock-ic-memo";
import { toICMemoView } from "../model/recommendation-adapter";
import { ActionStamp } from "./action-stamp";
import { DecisionActions } from "./decision-actions";
import { ReturnRangeBar } from "./return-range-bar";
import { SignalAgreementMatrix } from "./signal-agreement-matrix";

const REVIEW_STATUS: Record<PMReviewDecision, RecommendationStatus> = { approve: RecommendationStatus.APPROVED, reject: RecommendationStatus.REJECTED, defer: RecommendationStatus.DEFERRED };

export function ICMemoPanel() {
  const runId = useTerminalStore((state) => state.activeRunId);
  const activeTicker = useTerminalStore((state) => state.activeTicker);
  const role = useTerminalStore((state) => state.role);
  const recommendation = useRecommendation(runId);
  const conviction = useConviction(runId);
  const remote = Boolean(recommendation.data);
  const [mockStatus, setMockStatus] = useState(MOCK_IC_MEMO.status);
  const decision = usePMDecision(runId ?? "mock");

  if (recommendation.isLoading) return <FeatureLoading label="investment committee memo" />;
  if (recommendation.isError) return <FeatureError error={recommendation.error} retry={() => void recommendation.refetch()} />;

  const memo = recommendation.data ? toICMemoView(recommendation.data, activeTicker ?? "UNKNOWN", conviction.data) : { ...MOCK_IC_MEMO, status: mockStatus };

  function handleDecision(reviewDecision: PMReviewDecision, rationale: string) {
    if (remote && memo.reviewVersion) {
      decision.mutate({ decision: reviewDecision, rationale, expected_version: memo.reviewVersion });
      return;
    }
    setMockStatus(REVIEW_STATUS[reviewDecision]);
    useAuditStore.getState().addEntry({ actor_label: "PORTFOLIO MANAGER · FIXTURE", action: reviewDecision === "approve" ? AuditAction.APPROVE : reviewDecision === "reject" ? AuditAction.REJECT : AuditAction.UPDATE, summary: `Mock PM decision: ${reviewDecision.toUpperCase()} — ${rationale}`, reference: "FR-048" });
  }

  return (
    <Panel className="relative max-w-[900px] p-4">
      <div className="mb-4 flex items-start justify-between border-b border-hairline pb-3 pr-28">
        <div><h2 className="font-serif text-xl font-semibold">Investment Committee Memo</h2><p className="mt-1 font-mono text-[10px] text-text-faint">{memo.ticker} · {memo.company} · CONCLAVE v2.3</p></div>
        <div className="absolute top-4 right-4 flex flex-col items-end gap-1.5"><DataModeBadge remote={remote} refreshing={recommendation.isFetching} /><span className="font-mono text-[8px] text-parchment">INTERNAL — DECISION SUPPORT ONLY</span></div>
      </div>
      <ActionStamp action={memo.action} conviction={memo.conviction} />
      <p className="mb-5 max-w-[640px] font-serif text-[15px] leading-7 text-text-primary">{memo.thesis}</p>
      <div className="mb-5 grid grid-cols-2 gap-5"><div><SectionLabel icon={Calendar}>Time horizon</SectionLabel><p className="font-mono text-xs capitalize">{memo.timeHorizon}</p><p className="mt-1 text-[11px] text-text-dim">{memo.horizonDriver}</p></div><div><SectionLabel icon={Target}>Primary catalyst</SectionLabel><p className="font-mono text-xs">{memo.catalyst.name} — {memo.catalyst.date}</p><p className="mt-1 text-[11px] text-text-dim">{memo.catalyst.probability}% estimated probability</p></div></div>
      <SectionLabel icon={TrendingUp}>Expected return range</SectionLabel><ReturnRangeBar range={memo.expectedReturn} />
      <div className="my-5"><SectionLabel>Position sizing</SectionLabel><p className="font-mono text-xs">{memo.positionSizing}</p></div>
      <div className="mb-5"><SectionLabel>Signal agreement matrix</SectionLabel><SignalAgreementMatrix agreement={memo.agreement} /></div>
      <div className="mb-5 grid grid-cols-2 gap-5"><div><SectionLabel icon={AlertTriangle}>Key risk</SectionLabel><p className="text-xs leading-relaxed text-text-dim">{memo.keyRisk}</p></div><div><SectionLabel icon={XCircle}>Invalidation trigger</SectionLabel><p className="text-xs leading-relaxed text-text-dim">{memo.invalidation}</p></div></div>
      <DecisionActions status={memo.status} role={role} disabled={decision.isPending || (remote && !memo.reviewVersion)} onDecision={handleDecision} />
    </Panel>
  );
}
