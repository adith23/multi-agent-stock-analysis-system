import type { PerformanceResponse, PortfolioRisk, PortfolioState } from "@/entities/portfolio";
import type { JsonObject, JsonValue } from "@/shared/types";

import type { AllocationDatum, PerformanceDatum, RiskWaterfallDatum } from "../types/visualization.types";

function numericEntries(value: JsonObject): [string, number][] {
  return Object.entries(value).flatMap(([name, raw]): [string, number][] => {
    const number = typeof raw === "number" ? raw : typeof raw === "string" ? Number(raw) : Number.NaN;
    return Number.isFinite(number) ? [[name, number]] : [];
  });
}

export function toAllocationData(portfolio: PortfolioState): AllocationDatum[] {
  const source = Object.keys(portfolio.sector_exposures).length ? portfolio.sector_exposures : portfolio.weights;
  const entries = numericEntries(source).filter(([, value]) => value > 0);
  const total = entries.reduce((sum, [, value]) => sum + value, 0);
  if (!total) return [];
  return entries.map(([name, value]) => ({ name: humanize(name), value: (value / total) * 100 }));
}

export function toRiskWaterfallData(risk: PortfolioRisk): RiskWaterfallDatum[] {
  return numericEntries(risk.risk_metrics)
    .slice(0, 7)
    .map(([name, impact]) => ({ name: humanize(name), impact: normalizePercent(impact) }));
}

export function toPerformanceData(performance: PerformanceResponse): PerformanceDatum[] {
  return performance.records.slice(0, 8).reverse().map((record) => ({
    label: `${record.symbol} ${record.measurement_period}`,
    portfolio: normalizePercent(record.realized_return),
    benchmark: normalizePercent(record.benchmark_return),
    excess: normalizePercent(record.excess_return),
  }));
}

export function unwrapPerformanceResponse(data: PerformanceResponse | { results: JsonValue }): PerformanceResponse {
  if ("records" in data) return data;
  const results = data.results;
  if (isPerformanceResponse(results)) return results;
  return { summary: {}, records: [] };
}

function isPerformanceResponse(value: unknown): value is PerformanceResponse {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  return Array.isArray((value as { records?: unknown }).records);
}

function normalizePercent(value: number): number {
  return Math.abs(value) <= 1 ? value * 100 : value;
}

function humanize(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}
