import { describe, expect, it } from "vitest";

import { cn } from "@/shared/lib/cn";
import { formatCurrency, formatNumber, formatPercentage } from "@/shared/lib/formatters";

describe("shared utilities", () => {
  it("merges conditional and conflicting Tailwind classes", () => {
    expect(cn("px-2", false && "hidden", "px-4")).toBe("px-4");
  });

  it("formats numbers with deterministic locale options", () => {
    expect(formatNumber(1234.567, { locale: "en-US", maximumFractionDigits: 1 })).toBe("1,234.6");
  });

  it("formats decimal and percent inputs", () => {
    expect(formatPercentage(0.125, { locale: "en-US" })).toBe("12.5%");
    expect(formatPercentage(12.5, { locale: "en-US", input: "percent" })).toBe("12.5%");
  });

  it("returns an em dash for invalid currency values", () => {
    expect(formatCurrency("not-a-number")).toBe("—");
  });

  it("formats decimal strings as currency", () => {
    expect(formatCurrency("1234.5", "USD", { locale: "en-US" })).toBe("$1,234.50");
  });
});
