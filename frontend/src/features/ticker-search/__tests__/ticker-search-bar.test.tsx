import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TickerSearchBar } from "@/features/ticker-search";
import { useTerminalStore } from "@/stores/terminal-store";

describe("TickerSearchBar", () => {
  beforeEach(() => useTerminalStore.getState().resetTerminal());

  it("normalizes and submits a valid market symbol", () => {
    const onSubmit = vi.fn();
    render(<TickerSearchBar onSubmit={onSubmit} />);

    fireEvent.change(screen.getByRole("textbox", { name: "Ticker symbol" }), { target: { value: "brk.b" } });
    fireEvent.click(screen.getByRole("button", { name: "Go" }));

    expect(onSubmit).toHaveBeenCalledWith("BRK.B");
    expect(useTerminalStore.getState().tickerInput).toBe("BRK.B");
  });

  it("rejects malformed symbols and disables submission while running", () => {
    const onSubmit = vi.fn();
    const { rerender } = render(<TickerSearchBar onSubmit={onSubmit} />);
    const input = screen.getByRole("textbox", { name: "Ticker symbol" });

    fireEvent.change(input, { target: { value: ".BAD" } });
    expect(screen.getByRole("button", { name: "Go" })).toBeDisabled();

    useTerminalStore.getState().startAnalysis("AAPL", "test-run");
    rerender(<TickerSearchBar onSubmit={onSubmit} />);
    expect(screen.getByRole("button", { name: "Running" })).toBeDisabled();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
