import type { TickerQuote } from "../types/ticker.types";

/** Explicit Phase 3–4 fixture; live quotes are integrated in Phase 6. */
export const MOCK_TICKER_QUOTE: Readonly<TickerQuote> = {
  symbol: "HLXD",
  companyName: "Helios Dynamics Inc.",
  currency: "USD",
  price: 214.62,
  change: 3.18,
  changePercent: 1.51,
  intradayPoints: [207.8, 208.7, 208.1, 210.2, 209.7, 212.4, 211.9, 214.1, 214.62],
  asOf: "2026-08-26T09:41:31+05:30",
};

export function getMockQuote(symbol: string | null): Readonly<TickerQuote> | null {
  if (!symbol || symbol.toUpperCase() === MOCK_TICKER_QUOTE.symbol) return MOCK_TICKER_QUOTE;
  return null;
}
