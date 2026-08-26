import type { SVGAttributes } from "react";

import { cn } from "@/shared/lib/cn";

export interface SparklineProps extends Omit<SVGAttributes<SVGSVGElement>, "points"> {
  points: number[];
  color?: string;
  width?: number;
  height?: number;
  label?: string;
}

function toPolyline(points: number[], width: number, height: number): string {
  if (points.length === 0) return "";

  const minimum = Math.min(...points);
  const maximum = Math.max(...points);
  const range = maximum - minimum || 1;
  const xStep = points.length === 1 ? 0 : width / (points.length - 1);

  return points
    .map((point, index) => {
      const x = index * xStep;
      const y = height - ((point - minimum) / range) * height;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

export function Sparkline({
  points,
  color = "var(--color-green)",
  width = 96,
  height = 24,
  label = "Price trend",
  className,
  ...props
}: SparklineProps) {
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      className={cn("overflow-visible", className)}
      role="img"
      aria-label={label}
      {...props}
    >
      <polyline
        points={toPolyline(points, width, height)}
        fill="none"
        stroke={color}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
