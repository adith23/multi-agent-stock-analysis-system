import type { AllocationDatum, OhlcvPoint, PerformanceDatum, RiskWaterfallDatum } from "../types/visualization.types";

/** Fixture-only series: the current backend has an OHLCV model but no public read endpoint. */
export const MOCK_OHLCV: readonly OhlcvPoint[] = [
  { time: "2026-07-27", open: 188.2, high: 191.4, low: 186.7, close: 190.8, volume: 42_100_000 },
  { time: "2026-07-28", open: 190.7, high: 193.1, low: 189.5, close: 191.9, volume: 38_400_000 },
  { time: "2026-07-29", open: 192.1, high: 194.8, low: 190.8, close: 194.2, volume: 45_700_000 },
  { time: "2026-07-30", open: 194.4, high: 195.2, low: 190.3, close: 191.2, volume: 51_900_000 },
  { time: "2026-07-31", open: 191.0, high: 193.6, low: 189.8, close: 192.9, volume: 36_800_000 },
  { time: "2026-08-03", open: 193.2, high: 196.9, low: 192.7, close: 196.1, volume: 47_500_000 },
  { time: "2026-08-04", open: 196.3, high: 198.8, low: 195.4, close: 197.7, volume: 44_200_000 },
  { time: "2026-08-05", open: 197.5, high: 199.1, low: 194.9, close: 195.6, volume: 53_600_000 },
  { time: "2026-08-06", open: 195.4, high: 198.2, low: 194.6, close: 197.8, volume: 41_300_000 },
  { time: "2026-08-07", open: 198.0, high: 201.6, low: 197.5, close: 200.9, volume: 58_100_000 },
  { time: "2026-08-10", open: 201.1, high: 202.4, low: 198.7, close: 199.5, volume: 39_600_000 },
  { time: "2026-08-11", open: 199.7, high: 203.8, low: 199.1, close: 203.2, volume: 49_800_000 },
  { time: "2026-08-12", open: 203.4, high: 205.1, low: 201.6, close: 204.4, volume: 46_900_000 },
  { time: "2026-08-13", open: 204.1, high: 206.7, low: 202.8, close: 205.9, volume: 52_200_000 },
  { time: "2026-08-14", open: 206.0, high: 207.3, low: 203.9, close: 204.7, volume: 35_700_000 },
  { time: "2026-08-17", open: 204.9, high: 208.5, low: 204.2, close: 207.8, volume: 43_100_000 },
  { time: "2026-08-18", open: 208.1, high: 210.2, low: 206.6, close: 209.4, volume: 48_600_000 },
  { time: "2026-08-19", open: 209.2, high: 211.7, low: 207.4, close: 208.3, volume: 54_000_000 },
  { time: "2026-08-20", open: 208.5, high: 212.9, low: 208.0, close: 212.2, volume: 61_300_000 },
  { time: "2026-08-21", open: 212.4, high: 214.1, low: 210.7, close: 213.6, volume: 46_500_000 },
  { time: "2026-08-24", open: 213.8, high: 215.6, low: 211.9, close: 214.8, volume: 44_900_000 },
  { time: "2026-08-25", open: 214.6, high: 217.3, low: 213.5, close: 216.9, volume: 55_400_000 },
  { time: "2026-08-26", open: 217.1, high: 218.4, low: 214.8, close: 215.7, volume: 50_200_000 },
];

export const MOCK_ALLOCATION: readonly AllocationDatum[] = [
  { name: "Technology", value: 34 },
  { name: "Healthcare", value: 21 },
  { name: "Financials", value: 18 },
  { name: "Industrials", value: 15 },
  { name: "Other", value: 12 },
];

export const MOCK_RISK_WATERFALL: readonly RiskWaterfallDatum[] = [
  { name: "Market", impact: 38 },
  { name: "Factor", impact: 17 },
  { name: "Liquidity", impact: 11 },
  { name: "Hedge", impact: -9 },
  { name: "Residual", impact: 6 },
];

export const MOCK_PERFORMANCE: readonly PerformanceDatum[] = [
  { label: "1M", portfolio: 3.8, benchmark: 2.4, excess: 1.4 },
  { label: "3M", portfolio: 7.2, benchmark: 5.1, excess: 2.1 },
  { label: "6M", portfolio: 11.9, benchmark: 9.4, excess: 2.5 },
  { label: "12M", portfolio: 18.6, benchmark: 14.8, excess: 3.8 },
];
