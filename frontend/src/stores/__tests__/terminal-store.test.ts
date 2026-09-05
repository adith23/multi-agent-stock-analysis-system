import { beforeEach, describe, expect, it } from "vitest";

import { UserRole } from "@/entities/user";
import { initialTerminalState, useTerminalStore } from "@/stores/terminal-store";

describe("terminal store", () => {
  beforeEach(() => {
    useTerminalStore.getState().resetTerminal();
  });

  it("starts an analysis with normalized identifiers", () => {
    useTerminalStore.getState().startAnalysis(" aapl ", " run-123 ");

    expect(useTerminalStore.getState()).toMatchObject({
      activeTicker: "AAPL",
      activeRunId: "run-123",
      tickerInput: "AAPL",
      systemState: "running",
    });
  });

  it("rejects incomplete analysis context", () => {
    expect(() => useTerminalStore.getState().startAnalysis(" ", "run-123")).toThrow(
      "An analysis requires a ticker and run identifier.",
    );
  });

  it("updates navigation and backend-aligned role state", () => {
    const store = useTerminalStore.getState();
    store.setActiveTab("risk");
    store.setActiveSpecialist("technical");
    store.setRole(UserRole.RISK_OFFICER);

    expect(useTerminalStore.getState()).toMatchObject({
      activeTab: "risk",
      activeSpecialist: "technical",
      role: UserRole.RISK_OFFICER,
    });
  });

  it("clears transient run state on failure and fully resets", () => {
    useTerminalStore.getState().startAnalysis("MSFT", "run-456");
    useTerminalStore.getState().failAnalysis();
    expect(useTerminalStore.getState()).toMatchObject({
      activeTicker: "MSFT",
      activeRunId: null,
      systemState: "idle",
    });

    useTerminalStore.getState().resetTerminal();
    expect(useTerminalStore.getState()).toMatchObject(initialTerminalState);
  });
});
