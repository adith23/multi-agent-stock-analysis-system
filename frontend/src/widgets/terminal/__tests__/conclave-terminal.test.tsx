import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";

import { usePipelineStore } from "@/stores/pipeline-store";
import { useTerminalStore } from "@/stores/terminal-store";
import { ConclaveTerminal } from "@/widgets/terminal/conclave-terminal";

describe("ConclaveTerminal", () => {
  beforeEach(() => {
    usePipelineStore.getState().resetAllStages();
    useTerminalStore.getState().resetTerminal();
  });

  it("composes the complete terminal shell and default IC memo", () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity }, mutations: { retry: false } } });
    render(<QueryClientProvider client={queryClient}><ConclaveTerminal /></QueryClientProvider>);

    expect(screen.getByRole("banner", { name: "Terminal header" })).toBeVisible();
    expect(screen.getByRole("complementary", { name: "Agent pipeline" })).toBeVisible();
    expect(screen.getByRole("region", { name: "Terminal workspace" })).toBeVisible();
    expect(screen.getByRole("complementary", { name: "Portfolio context" })).toBeVisible();
    expect(screen.getByRole("contentinfo", { name: "Terminal status" })).toBeVisible();
    expect(screen.getByRole("tab", { name: "IC Memo" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("HLXD")).toBeVisible();
  });
});
