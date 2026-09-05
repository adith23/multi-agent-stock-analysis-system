import { create } from "zustand";

import { UserRole } from "@/entities/user/types";

export type TerminalTab = "overview" | "specialists" | "adversarial" | "risk" | "analytics" | "audit";
export type ActiveSpecialist = "macro" | "fundamental" | "technical" | "sentiment";
export type SystemState = "idle" | "running" | "ready";

export interface TerminalState {
  activeTab: TerminalTab;
  activeSpecialist: ActiveSpecialist;
  role: UserRole;
  tickerInput: string;
  activeTicker: string | null;
  activeRunId: string | null;
  systemState: SystemState;
  setActiveTab: (tab: TerminalTab) => void;
  setActiveSpecialist: (specialist: ActiveSpecialist) => void;
  setRole: (role: UserRole) => void;
  setTickerInput: (input: string) => void;
  startAnalysis: (ticker: string, runId: string) => void;
  completeAnalysis: () => void;
  failAnalysis: () => void;
  resetTerminal: () => void;
}

export type TerminalDataState = Pick<
  TerminalState,
  | "activeTab"
  | "activeSpecialist"
  | "role"
  | "tickerInput"
  | "activeTicker"
  | "activeRunId"
  | "systemState"
>;

export const initialTerminalState: Readonly<TerminalDataState> = {
  activeTab: "overview",
  activeSpecialist: "macro",
  role: UserRole.RESEARCH_ANALYST,
  tickerInput: "",
  activeTicker: null,
  activeRunId: null,
  systemState: "idle",
};

function normalizeTicker(ticker: string): string {
  return ticker.trim().toUpperCase();
}

export const useTerminalStore = create<TerminalState>()((set) => ({
  ...initialTerminalState,
  setActiveTab: (activeTab) => set({ activeTab }),
  setActiveSpecialist: (activeSpecialist) => set({ activeSpecialist }),
  setRole: (role) => set({ role }),
  setTickerInput: (input) => set({ tickerInput: input.toUpperCase() }),
  startAnalysis: (ticker, runId) => {
    const activeTicker = normalizeTicker(ticker);
    const normalizedRunId = runId.trim();
    if (!activeTicker || !normalizedRunId) {
      throw new Error("An analysis requires a ticker and run identifier.");
    }

    set({
      activeTicker,
      activeRunId: normalizedRunId,
      tickerInput: activeTicker,
      systemState: "running",
    });
  },
  completeAnalysis: () => set({ systemState: "ready" }),
  failAnalysis: () => set({ activeRunId: null, systemState: "idle" }),
  resetTerminal: () => set(initialTerminalState),
}));
