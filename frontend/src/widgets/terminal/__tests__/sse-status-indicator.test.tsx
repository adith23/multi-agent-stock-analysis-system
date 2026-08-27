import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SseStatusIndicator, summarizeStatus } from "@/widgets/terminal/sse-status-indicator";

describe("SseStatusIndicator", () => {
  it("prioritizes degraded and reconnecting states", () => {
    expect(summarizeStatus("open", "error")).toBe("error");
    expect(summarizeStatus("open", "reconnecting")).toBe("reconnecting");
    expect(summarizeStatus("idle", "open")).toBe("open");
  });

  it("exposes the connection state accessibly", () => {
    render(<SseStatusIndicator pipeline="open" alerts="open" />);
    expect(screen.getByLabelText("SSE live")).toBeVisible();
    expect(screen.getByText("SSE live")).toHaveClass("text-green");
  });
});
