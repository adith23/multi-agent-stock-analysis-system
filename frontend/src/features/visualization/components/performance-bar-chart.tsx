"use client";

import { Bar, BarChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { PerformanceDatum } from "../types/visualization.types";
import { ChartEmptyState } from "./chart-empty-state";

export function PerformanceBarChart({ data }: { data: readonly PerformanceDatum[] }) {
  if (!data.length) return <ChartEmptyState label="performance attribution" />;
  return (
    <div className="h-64" role="img" aria-label="Performance attribution bar chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={[...data]} margin={{ top: 8, right: 8, bottom: 24, left: -12 }}>
          <CartesianGrid stroke="#242830" vertical={false} />
          <XAxis dataKey="label" stroke="#5c616b" tick={{ fontSize: 8 }} angle={-20} textAnchor="end" />
          <YAxis stroke="#5c616b" tick={{ fontSize: 8 }} unit="%" />
          <Tooltip contentStyle={{ background: "#181b21", border: "1px solid #3a3f4a", fontSize: 11 }} />
          <Legend wrapperStyle={{ fontSize: 9, fontFamily: "IBM Plex Mono" }} />
          <ReferenceLine y={0} stroke="#9ba0aa" />
          <Bar name="Portfolio" dataKey="portfolio" fill="#e0a730" radius={[2, 2, 0, 0]} />
          <Bar name="Benchmark" dataKey="benchmark" fill="#6fa8dc" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
