"use client";

import { useEffect, useRef, useState } from "react";
import { AreaSeries, CandlestickSeries, ColorType, createChart, type Time } from "lightweight-charts";

import { cn } from "@/shared/lib";

import type { OhlcvPoint } from "../types/visualization.types";
import { ChartEmptyState } from "./chart-empty-state";

export function PriceChart({ data, symbol }: { data: readonly OhlcvPoint[]; symbol: string }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<"candlestick" | "area">("candlestick");

  useEffect(() => {
    const host = hostRef.current;
    if (!host || !data.length) return;

    const chart = createChart(host, {
      width: host.clientWidth,
      height: 256,
      layout: { background: { type: ColorType.Solid, color: "#111318" }, textColor: "#9ba0aa", attributionLogo: false },
      grid: { vertLines: { color: "#242830" }, horzLines: { color: "#242830" } },
      rightPriceScale: { borderColor: "#3a3f4a" },
      timeScale: { borderColor: "#3a3f4a", timeVisible: true },
      crosshair: { vertLine: { color: "#7a5e22" }, horzLine: { color: "#7a5e22" } },
    });

    if (mode === "candlestick") {
      const series = chart.addSeries(CandlestickSeries, { upColor: "#3fb968", downColor: "#f0554a", borderVisible: false, wickUpColor: "#3fb968", wickDownColor: "#f0554a" });
      series.setData(data.map(({ time, open, high, low, close }) => ({ time: time as Time, open, high, low, close })));
    } else {
      const series = chart.addSeries(AreaSeries, { lineColor: "#e0a730", topColor: "rgba(224, 167, 48, 0.28)", bottomColor: "rgba(224, 167, 48, 0.01)" });
      series.setData(data.map(({ time, close }) => ({ time: time as Time, value: close })));
    }
    chart.timeScale().fitContent();

    const observer = new ResizeObserver(([entry]) => chart.applyOptions({ width: entry.contentRect.width }));
    observer.observe(host);
    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [data, mode]);

  if (!data.length) return <ChartEmptyState label="price" />;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <p className="font-mono text-[10px] text-text-dim">{symbol} · DAILY OHLCV</p>
        <div className="flex rounded-terminal border border-hairline bg-inset p-0.5" aria-label="Price chart style">
          {(["candlestick", "area"] as const).map((value) => <button key={value} type="button" onClick={() => setMode(value)} className={cn("rounded-sm px-2 py-1 font-mono text-[8px] uppercase", mode === value ? "bg-amber/15 text-amber" : "text-text-faint")} aria-pressed={mode === value}>{value}</button>)}
        </div>
      </div>
      <div ref={hostRef} className="h-64 w-full" role="img" aria-label={`${symbol} ${mode} price chart`} />
      <p className="mt-1 text-right font-mono text-[7px] text-text-faint">Charts by <a className="underline hover:text-text-dim" href="https://www.tradingview.com/" target="_blank" rel="noreferrer">TradingView</a></p>
    </div>
  );
}
