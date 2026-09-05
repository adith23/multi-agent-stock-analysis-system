export interface TickerQuote {
  symbol: string;
  companyName: string;
  currency: "USD";
  price: number;
  change: number;
  changePercent: number;
  intradayPoints: readonly number[];
  asOf: string;
}
