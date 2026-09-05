import { fireEvent, render, screen } from "@testing-library/react";
import { Activity } from "lucide-react";
import { describe, expect, it, vi } from "vitest";

import { AgentStance } from "@/entities/agent";
import {
  ActionButton,
  Chip,
  DataModeBadge,
  FeatureError,
  FeatureErrorBoundary,
  FeatureLoading,
  Meter,
  Panel,
  SectionLabel,
  Skeleton,
  Sparkline,
  StanceIcon,
} from "@/shared/ui";

function RenderFailure({ fail }: { fail: boolean }) {
  if (fail) throw new Error("Panel exploded");
  return <p>Recovered panel</p>;
}

describe("terminal design-system primitives", () => {
  it("composes semantic terminal surfaces", () => {
    render(
      <Panel aria-label="Analysis panel">
        <SectionLabel icon={Activity}>Health</SectionLabel>
        <Chip>Ready</Chip>
        <Skeleton data-testid="skeleton" className="h-4" />
      </Panel>,
    );

    expect(screen.getByRole("region", { name: "Analysis panel" })).toHaveClass("bg-panel");
    expect(screen.getByRole("heading", { name: "Health" })).toBeVisible();
    expect(screen.getByText("Ready")).toHaveClass("font-mono");
    expect(screen.getByTestId("skeleton")).toHaveAttribute("aria-hidden", "true");
  });

  it("exposes bounded meter semantics and threshold colors", () => {
    const { rerender } = render(<Meter value={41} />);
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "41");
    expect(screen.getByRole("progressbar").firstElementChild).toHaveStyle({
      backgroundColor: "var(--color-green)",
    });

    rerender(<Meter value={95} limit={100} />);
    expect(screen.getByRole("progressbar").firstElementChild).toHaveStyle({
      backgroundColor: "var(--color-red)",
    });
  });

  it("renders accessible stance and sparkline graphics", () => {
    render(
      <>
        <StanceIcon stance={AgentStance.BULLISH} />
        <Sparkline points={[10, 12, 11, 15]} label="Four-day trend" />
      </>,
    );

    expect(screen.getByRole("img", { name: "Bullish" })).toHaveClass("text-green");
    expect(screen.getByRole("img", { name: "Four-day trend" }).querySelector("polyline")).toHaveAttribute(
      "points",
      expect.stringContaining(","),
    );
  });

  it("honors standard button behavior", () => {
    const onClick = vi.fn();
    render(<ActionButton onClick={onClick}>Run</ActionButton>);

    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    expect(onClick).toHaveBeenCalledOnce();
    expect(screen.getByRole("button", { name: "Run" })).toHaveAttribute("type", "button");
  });

  it("renders loading, data provenance, and retryable feature errors", () => {
    const retry = vi.fn();
    const { rerender } = render(<FeatureLoading label="analysis" />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading analysis");

    rerender(<DataModeBadge remote={false} />);
    expect(screen.getByText("Typed fixture")).toBeVisible();
    rerender(<DataModeBadge remote refreshing />);
    expect(screen.getByText("Refreshing API")).toBeVisible();

    rerender(<FeatureError error={new Error("Network unavailable")} retry={retry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Network unavailable");
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(retry).toHaveBeenCalledOnce();
  });

  it("contains panel failures and resets when the workspace changes", () => {
    const onError = vi.fn();
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const { rerender } = render(
      <FeatureErrorBoundary resetKey="overview" onError={onError}>
        <RenderFailure fail />
      </FeatureErrorBoundary>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/could not be rendered/i);
    expect(onError).toHaveBeenCalledOnce();

    rerender(
      <FeatureErrorBoundary resetKey="risk" onError={onError}>
        <RenderFailure fail={false} />
      </FeatureErrorBoundary>,
    );
    expect(screen.getByText("Recovered panel")).toBeVisible();
    consoleError.mockRestore();
  });
});
