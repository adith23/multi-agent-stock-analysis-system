import { create } from "zustand";

import type { AuditEntry } from "@/entities/audit/types";

export type NewAuditEntry = Omit<AuditEntry, "id" | "occurred_at" | "sync_status"> &
  Partial<Pick<AuditEntry, "id" | "occurred_at" | "sync_status">>;

export interface AuditState {
  entries: AuditEntry[];
  addEntry: (entry: NewAuditEntry) => AuditEntry;
  setEntries: (entries: AuditEntry[]) => void;
  clearEntries: () => void;
}

function createClientId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `audit-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export const useAuditStore = create<AuditState>()((set) => ({
  entries: [],
  addEntry: (entry) => {
    const createdEntry: AuditEntry = {
      ...entry,
      id: entry.id ?? createClientId(),
      occurred_at: entry.occurred_at ?? new Date().toISOString(),
      sync_status: entry.sync_status ?? "pending",
    };
    set((state) => ({ entries: [createdEntry, ...state.entries] }));
    return createdEntry;
  },
  setEntries: (entries) => set({ entries: [...entries] }),
  clearEntries: () => set({ entries: [] }),
}));
