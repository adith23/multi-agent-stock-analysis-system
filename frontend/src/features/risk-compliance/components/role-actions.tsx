import { AuditAction } from "@/entities/audit";
import { UserRole } from "@/entities/user";
import { ActionButton } from "@/shared/ui";
import { useAuditStore } from "@/stores/audit-store";

export function RoleActions({ role, remote }: { role: UserRole; remote: boolean }) {
  if (remote && (role === UserRole.RISK_OFFICER || role === UserRole.COMPLIANCE_REVIEWER)) return <span className="font-mono text-[9px] text-text-faint">Action unavailable — backend mutation endpoint not implemented</span>;
  if (role === UserRole.RISK_OFFICER) return <ActionButton color="var(--color-amber)" onClick={() => useAuditStore.getState().addEntry({ actor_label: "RISK OFFICER · FIXTURE", action: AuditAction.OVERRIDE, summary: "Mock risk constraint override recorded", reference: "NFR-020" })}>Override constraint</ActionButton>;
  if (role === UserRole.COMPLIANCE_REVIEWER) return <ActionButton color="var(--color-red)" onClick={() => useAuditStore.getState().addEntry({ actor_label: "COMPLIANCE REVIEWER · FIXTURE", action: AuditAction.ESCALATE, summary: "Mock recommendation escalation recorded", reference: "NFR-018" })}>Escalate</ActionButton>;
  return <span className="font-mono text-[9px] text-text-faint">Read-only for current role</span>;
}
