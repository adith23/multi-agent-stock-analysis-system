export function ChartEmptyState({ label }: { label: string }) {
  return <div className="grid h-64 place-items-center border border-dashed border-hairline font-mono text-[10px] text-text-faint">No {label} data available</div>;
}
