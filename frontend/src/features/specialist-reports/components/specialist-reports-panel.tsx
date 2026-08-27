import { AgentStance, type SpecialistReport } from "@/entities/agent";
import { DataModeBadge, FeatureError, FeatureLoading, Panel, SectionLabel, StanceIcon } from "@/shared/ui";
import { cn } from "@/shared/lib";
import { useTerminalStore, type ActiveSpecialist } from "@/stores/terminal-store";
import { useSpecialistReports } from "../hooks/use-specialist-reports";
import { MOCK_SPECIALIST_REPORTS } from "../model/mock-specialists";
import { FundamentalReport, MacroReport, SentimentReport, TechnicalReport } from "./specialist-report-views";

const TABS: readonly ActiveSpecialist[] = ["macro", "fundamental", "technical", "sentiment"];

function RemoteSpecialistReport({ report }: { report: SpecialistReport }) {
  return <Panel><div className="flex items-center justify-between"><SectionLabel>{report.specialist} specialist output</SectionLabel><span className="flex items-center gap-1 font-mono text-[10px] capitalize text-text-dim"><StanceIcon stance={report.stance || AgentStance.NEUTRAL} />{report.stance || "unclassified"} · {(report.confidence * 100).toFixed(0)}%</span></div><h3 className="font-serif text-sm">{report.thesis}</h3><p className="mt-3 text-xs leading-6 text-text-dim">{report.summary}</p><div className="mt-4 grid grid-cols-2 gap-5"><div><h4 className="font-mono text-[9px] text-text-faint uppercase">Assumptions</h4><pre className="mt-1 whitespace-pre-wrap font-sans text-[11px] leading-relaxed text-text-dim">{JSON.stringify(report.assumptions, null, 2)}</pre></div><div><h4 className="font-mono text-[9px] text-text-faint uppercase">Limitations</h4><pre className="mt-1 whitespace-pre-wrap font-sans text-[11px] leading-relaxed text-text-dim">{JSON.stringify(report.limitations, null, 2)}</pre></div></div><div className="mt-4 border-t border-hairline pt-2 font-mono text-[9px] text-text-faint">Agent {report.agent_version} · Model {report.model_version} · Prompt {report.prompt_version} · v{report.version}</div></Panel>;
}

export function SpecialistReportsPanel() {
  const activeSpecialist = useTerminalStore((state) => state.activeSpecialist);
  const setActiveSpecialist = useTerminalStore((state) => state.setActiveSpecialist);
  const runId = useTerminalStore((state) => state.activeRunId);
  const query = useSpecialistReports(runId);
  const remote = Boolean(query.data);

  if (query.isLoading) return <FeatureLoading label="specialist reports" />;
  if (query.isError) return <FeatureError error={query.error} retry={() => void query.refetch()} />;
  const remoteReport = query.data?.find((report) => report.specialist === activeSpecialist);

  return <div className="max-w-[900px]"><div className="mb-3 flex items-center justify-between"><div className="flex gap-1.5" role="tablist" aria-label="Specialist reports">{TABS.map((specialist) => <button key={specialist} type="button" role="tab" aria-selected={activeSpecialist === specialist} className={cn("rounded-terminal border border-hairline px-3 py-1.5 font-mono text-[10px] capitalize", activeSpecialist === specialist ? "bg-panel-raised text-text-primary" : "text-text-dim hover:text-text-primary")} onClick={() => setActiveSpecialist(specialist)}>{specialist}</button>)}</div><DataModeBadge remote={remote} refreshing={query.isFetching} /></div>{remote ? remoteReport ? <RemoteSpecialistReport report={remoteReport} /> : <FeatureError error={new Error(`The backend returned no ${activeSpecialist} report for this run.`)} /> : activeSpecialist === "macro" ? <MacroReport report={MOCK_SPECIALIST_REPORTS.macro} /> : activeSpecialist === "fundamental" ? <FundamentalReport report={MOCK_SPECIALIST_REPORTS.fundamental} /> : activeSpecialist === "technical" ? <TechnicalReport report={MOCK_SPECIALIST_REPORTS.technical} /> : <SentimentReport report={MOCK_SPECIALIST_REPORTS.sentiment} />}</div>;
}
