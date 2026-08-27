"use client";

import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { RiskWaterfallDatum } from "../types/visualization.types";
import { ChartEmptyState } from "./chart-empty-state";

export function RiskWaterfallChart({ data }: { data: readonly RiskWaterfallDatum[] }) {
  if (!data.length) return <ChartEmptyState label="risk budget" />;
  const ranges = data.map((item, index) => {
    const previous = data.slice(0, index).reduce((total, entry) => total + entry.impact, 0);
    const current = previous + item.impact;
    return { ...item, range: [Math.min(previous, current), Math.max(previous, current)] };
  });

  return (
    <div className="h-64" role="img" aria-label="Risk budget waterfall chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={ranges} margin={{ top: 8, right: 8, bottom: 24, left: -12 }}>
          <CartesianGrid stroke="#242830" vertical={false} />
          <XAxis dataKey="name" stroke="#5c616b" tick={{ fontSize: 8 }} angle={-20} textAnchor="end" />
          <YAxis stroke="#5c616b" tick={{ fontSize: 8 }} unit="%" />
          <Tooltip contentStyle={{ background: "#181b21", border: "1px solid #3a3f4a", fontSize: 11 }} />
          <ReferenceLine y={0} stroke="#9ba0aa" />
          <Bar dataKey="range" radius={2}>
            {ranges.map((item) => <Cell key={item.name} fill={item.impact >= 0 ? "#f0554a" : "#3fb968"} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
