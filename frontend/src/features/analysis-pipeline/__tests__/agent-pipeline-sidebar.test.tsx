import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { AgentPipelineSidebar } from "@/features/analysis-pipeline";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useTerminalStore } from "@/stores/terminal-store";

describe("AgentPipelineSidebar", () => {
  beforeEach(() => {
    usePipelineStore.getState().resetAllStages();
    useTerminalStore.getState().resetTerminal();
  });

  it("groups every pipeline stage and exposes its status", () => {
    render(<AgentPipelineSidebar />);

    expect(screen.getByRole("navigation", { name: "Pipeline stages" })).toBeVisible();
    expect(screen.getByRole("button", { name: /Technical/ })).toBeVisible();
    expect(screen.getByRole("img", { name: "Technical: Pending" })).toBeVisible();
    expect(screen.getByText("0/9 complete")).toBeVisible();
  });

  it("routes specialist stages through terminal state", () => {
    render(<AgentPipelineSidebar />);
    fireEvent.click(screen.getByRole("button", { name: /Technical/ }));

    expect(useTerminalStore.getState()).toMatchObject({
      activeTab: "specialists",
      activeSpecialist: "technical",
    });
  });
});
