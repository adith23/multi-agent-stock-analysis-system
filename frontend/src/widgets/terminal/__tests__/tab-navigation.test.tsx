import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { TabNavigation } from "@/widgets/terminal/tab-navigation";
import { useTerminalStore } from "@/stores/terminal-store";

describe("TabNavigation", () => {
  beforeEach(() => useTerminalStore.getState().resetTerminal());

  it("drives the five terminal views through the terminal store", () => {
    render(<TabNavigation />);
    const riskTab = screen.getByRole("tab", { name: "Risk + Compliance" });

    fireEvent.click(riskTab);

    expect(riskTab).toHaveAttribute("aria-selected", "true");
    expect(useTerminalStore.getState().activeTab).toBe("risk");
    expect(screen.getAllByRole("tab")).toHaveLength(5);
  });
});
