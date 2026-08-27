import { AuditAction, type AuditEntry } from "@/entities/audit";

export const MOCK_AUDIT_ENTRIES: readonly AuditEntry[] = [
  { id: "fixture-pm", occurred_at: "2026-08-26T09:41:22+05:30", actor_label: "SYSTEM · FIXTURE", action: AuditAction.CREATE, summary: "PM Agent produced recommendation for HLXD", reference: "FR-052", sync_status: "synced" },
  { id: "fixture-risk", occurred_at: "2026-08-26T09:41:18+05:30", actor_label: "SYSTEM · FIXTURE", action: AuditAction.EXECUTE, summary: "Risk Manager evaluated the portfolio risk budget", reference: "FR-041", sync_status: "synced" },
  { id: "fixture-debate", occurred_at: "2026-08-26T09:41:09+05:30", actor_label: "SYSTEM · FIXTURE", action: AuditAction.EXECUTE, summary: "Bull vs. Bear Agent generated a decision memo", reference: "FR-038", sync_status: "synced" },
  { id: "fixture-specialists", occurred_at: "2026-08-26T09:40:51+05:30", actor_label: "SYSTEM · FIXTURE", action: AuditAction.EXECUTE, summary: "Specialist agent outputs completed", reference: "FR-008–033", sync_status: "synced" },
  { id: "fixture-data", occurred_at: "2026-08-26T09:40:12+05:30", actor_label: "SYSTEM · FIXTURE", action: AuditAction.CREATE, summary: "Data Collector normalized 1,204 records from 14 sources", reference: "FR-003", sync_status: "synced" },
];
