import type { ReturnRangeView } from "../types/ic-memo.types";

export function ReturnRangeBar({ range }: { range: ReturnRangeView }) {
  return <div className="relative h-7 overflow-hidden rounded-terminal border border-hairline bg-inset font-mono text-[10px]" aria-label={`Expected return: bear ${range.bear}%, base ${range.base}%, bull ${range.bull}%`}><div className="absolute inset-y-0 left-0 w-1/2 border-r border-green bg-green/10" aria-hidden="true" /><span className="absolute top-1.5 left-2 text-red">BEAR {range.bear}%</span><strong className="absolute top-1.5 left-1/2 -translate-x-1/2 text-text-primary">BASE {range.base >= 0 ? "+" : ""}{range.base}%</strong><span className="absolute top-1.5 right-2 text-green">BULL {range.bull >= 0 ? "+" : ""}{range.bull}%</span></div>;
}
