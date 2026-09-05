import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { TabNavigation } from "@/widgets/terminal/tab-navigation";
import { useTerminalStore } from "@/stores/terminal-store";

describe("TabNavigation", () => {
  beforeEach(() => useTerminalStore.getState().resetTerminal());

  it("drives the six terminal views through the terminal store", () => {
    render(<TabNavigation />);
    const riskTab = screen.getByRole("tab", { name: "Risk + Compliance" });

    fireEvent.click(riskTab);

    expect(riskTab).toHaveAttribute("aria-selected", "true");
    expect(useTerminalStore.getState().activeTab).toBe("risk");
    expect(screen.getAllByRole("tab")).toHaveLength(6);
  });

  it("supports roving focus with arrow, Home, and End keys", () => {
    render(<TabNavigation />);
    const tabs = screen.getAllByRole("tab");

    tabs[0].focus();
    fireEvent.keyDown(tabs[0], { key: "ArrowRight" });
    expect(tabs[1]).toHaveFocus();
    expect(tabs[1]).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(tabs[1], { key: "End" });
    expect(tabs[5]).toHaveFocus();
    expect(useTerminalStore.getState().activeTab).toBe("audit");

    fireEvent.keyDown(tabs[5], { key: "Home" });
    expect(tabs[0]).toHaveFocus();
  });
});
