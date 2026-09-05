import { beforeEach, describe, expect, it } from "vitest";

import { AuditAction, type AuditEntry } from "@/entities/audit";
import { useAuditStore } from "@/stores/audit-store";

describe("audit store", () => {
  beforeEach(() => {
    useAuditStore.getState().clearEntries();
  });

  it("prepends a timestamped optimistic entry", () => {
    const created = useAuditStore.getState().addEntry({
      actor_label: "SYSTEM",
      action: AuditAction.EXECUTE,
      summary: "Analysis dispatched",
      reference: "run-1",
    });

    expect(created.id).toBeTruthy();
    expect(created.occurred_at).toBeTruthy();
    expect(created.sync_status).toBe("pending");
    expect(useAuditStore.getState().entries[0]).toEqual(created);
  });

  it("replaces entries without retaining the caller array", () => {
    const entries: AuditEntry[] = [
      {
        id: "audit-1",
        occurred_at: "2026-08-26T00:00:00.000Z",
        actor_label: "PM",
        action: AuditAction.APPROVE,
        summary: "Recommendation approved",
        reference: "run-1",
        sync_status: "synced",
      },
    ];

    useAuditStore.getState().setEntries(entries);
    expect(useAuditStore.getState().entries).toEqual(entries);
    expect(useAuditStore.getState().entries).not.toBe(entries);
  });
});
