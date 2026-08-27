export interface OhlcvPoint {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface AllocationDatum {
  name: string;
  value: number;
}

export interface RiskWaterfallDatum {
  name: string;
  impact: number;
}

export interface PerformanceDatum {
  label: string;
  portfolio: number;
  benchmark: number;
  excess: number;
}
