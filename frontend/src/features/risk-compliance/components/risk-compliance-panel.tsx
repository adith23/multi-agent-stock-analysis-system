import { Gavel, ShieldAlert } from "lucide-react";
import type { RiskComplianceResponse } from "@/entities/risk";
import type { JsonValue } from "@/shared/types";
import { Chip, DataModeBadge, FeatureError, FeatureLoading, Panel, SectionLabel } from "@/shared/ui";
import { useTerminalStore } from "@/stores/terminal-store";
import { useRiskCompliance } from "../hooks/use-risk-compliance";
import { MOCK_RISK_COMPLIANCE } from "../model/mock-risk-compliance";
import type { ComplianceCheckView, RiskComplianceView } from "../types/risk-compliance.types";
import { ComplianceChecklist } from "./compliance-checklist";
import { ExposureMeters } from "./exposure-meters";
import { RoleActions } from "./role-actions";
import { StressTestTable } from "./stress-test-table";

function display(value: JsonValue): string { return typeof value === "string" ? value : JSON.stringify(value); }
function fromRemote(response: RiskComplianceResponse): RiskComplianceView {
  const exposures = Object.entries(response.risk.risk_metrics).flatMap(([label, value]) => typeof value === "number" ? [{ label: label.replaceAll("_", " "), value, limit: 100 }] : []);
  const stressTests = Object.entries(response.risk.scenario_results).map(([scenario, impact]) => ({ scenario: scenario.replaceAll("_", " "), impact: display(impact) }));
  const checks: ComplianceCheckView[] = response.compliance.checks.map((value, index) => {
    if (value && typeof value === "object" && !Array.isArray(value)) return { label: typeof value.label === "string" ? value.label : `Compliance check ${index + 1}`, pass: value.pass === true };
    return { label: display(value), pass: response.compliance.passed };
  });
  return { status: response.risk.decision.replaceAll("_", " ").toUpperCase(), exposures, stressTests, note: response.risk.rationale, restrictedListStatus: response.compliance.restricted_list_match ? "MATCH" : "CLEAR", checks, escalation: response.compliance.approval_required ? "REQUIRED" : "NONE" };
}

export function RiskCompliancePanel() {
  const runId = useTerminalStore((state) => state.activeRunId);
  const role = useTerminalStore((state) => state.role);
  const query = useRiskCompliance(runId);
  if (query.isLoading) return <FeatureLoading label="risk and compliance package" />;
  if (query.isError) return <FeatureError error={query.error} retry={() => void query.refetch()} />;
  const remote = Boolean(query.data);
  const data = query.data ? fromRemote(query.data) : MOCK_RISK_COMPLIANCE;
  return <div className="max-w-[900px]"><Panel className="mb-3 flex items-center gap-3" borderColor="color-mix(in srgb, var(--color-amber) 45%, transparent)"><ShieldAlert className="size-5 text-amber" aria-hidden="true" /><strong className="font-mono text-xs">{data.status}</strong><div className="ml-auto flex items-center gap-2"><DataModeBadge remote={remote} refreshing={query.isFetching} /><RoleActions role={role} remote={remote} /></div></Panel><Panel className="mb-3"><SectionLabel>Exposure vs. limit</SectionLabel>{data.exposures.length ? <ExposureMeters exposures={data.exposures} /> : <p className="text-xs text-text-faint">No scalar exposure metrics supplied.</p>}<p className="mt-4 text-xs leading-6 text-text-dim">{data.note}</p></Panel><Panel className="mb-3"><SectionLabel>Stress test scenarios</SectionLabel>{data.stressTests.length ? <StressTestTable scenarios={data.stressTests} /> : <p className="text-xs text-text-faint">No stress scenarios supplied.</p>}</Panel><Panel><div className="flex items-center justify-between"><SectionLabel icon={Gavel}>Compliance</SectionLabel><Chip color={data.restrictedListStatus === "CLEAR" ? "var(--color-green)" : "var(--color-red)"}>Restricted list: {data.restrictedListStatus}</Chip></div><ComplianceChecklist checks={data.checks} /><div className="mt-3"><Chip>Escalation: {data.escalation}</Chip></div></Panel></div>;
}
