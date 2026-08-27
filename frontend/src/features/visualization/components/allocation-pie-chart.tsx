"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { AllocationDatum } from "../types/visualization.types";
import { ChartEmptyState } from "./chart-empty-state";

const COLORS = ["#e0a730", "#6fa8dc", "#3fb968", "#c9a66b", "#7a5e22", "#9ba0aa"];

export function AllocationPieChart({ data }: { data: readonly AllocationDatum[] }) {
  if (!data.length) return <ChartEmptyState label="allocation" />;
  return (
    <div className="h-64" role="img" aria-label="Portfolio allocation pie chart">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={[...data]} dataKey="value" nameKey="name" innerRadius="48%" outerRadius="74%" paddingAngle={2} stroke="#111318">
            {data.map((entry, index) => <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />)}
          </Pie>
          <Tooltip contentStyle={{ background: "#181b21", border: "1px solid #3a3f4a", fontSize: 11 }} />
          <Legend wrapperStyle={{ fontSize: 9, fontFamily: "IBM Plex Mono" }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
