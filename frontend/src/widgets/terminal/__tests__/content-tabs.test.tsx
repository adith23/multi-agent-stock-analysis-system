import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { UserRole } from "@/entities/user";
import { useAuditStore } from "@/stores/audit-store";
import { useTerminalStore } from "@/stores/terminal-store";
import { TerminalBody } from "@/widgets/terminal/terminal-body";

function renderBody() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } });
  return render(<QueryClientProvider client={client}><TerminalBody leftSidebar={null} rightSidebar={null} /></QueryClientProvider>);
}

describe("terminal content tabs", () => {
  beforeEach(() => { useTerminalStore.getState().resetTerminal(); useAuditStore.getState().clearEntries(); });

  it("renders every typed fixture module through terminal navigation", () => {
    renderBody();
    expect(screen.getByRole("heading", { name: "Investment Committee Memo" })).toBeVisible();
    fireEvent.click(screen.getByRole("tab", { name: "Specialist Reports" }));
    expect(screen.getByText("Risk-On / Late-Cycle")).toBeVisible();
    fireEvent.click(screen.getByRole("tab", { name: "Bull vs. Bear" }));
    expect(screen.getByRole("heading", { name: "Bull case" })).toBeVisible();
    fireEvent.click(screen.getByRole("tab", { name: "Risk + Compliance" }));
    expect(screen.getByText("PASS WITH CONDITIONS")).toBeVisible();
    fireEvent.click(screen.getByRole("tab", { name: "Audit" }));
    expect(screen.getByRole("table", { name: "Audit trail" })).toBeVisible();
  });

  it("enforces role visibility and records fixture decisions in the audit store", () => {
    renderBody();
    expect(screen.getByText(/Portfolio Manager role required/)).toBeVisible();
    act(() => useTerminalStore.getState().setRole(UserRole.PORTFOLIO_MANAGER));
    fireEvent.change(screen.getByPlaceholderText("Required by the review contract"), { target: { value: "Approved within the documented risk budget." } });
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(useAuditStore.getState().entries[0].summary).toContain("APPROVE");
  });
});
