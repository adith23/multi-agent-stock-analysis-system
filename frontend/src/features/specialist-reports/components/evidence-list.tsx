import type { EvidenceItem } from "../types/specialist.types";

const CONFIDENCE_COLOR = { High: "text-green", Med: "text-amber", Low: "text-text-faint" } as const;

export function EvidenceList({ items }: { items: readonly EvidenceItem[] }) {
  return <section className="mt-4 border-t border-hairline pt-2" aria-label="Evidence and provenance"><h3 className="mb-1 font-mono text-[9px] tracking-[0.1em] text-text-faint uppercase">Evidence &amp; provenance</h3>{items.length ? items.map((item, index) => <div key={`${item.source}-${index}`} className="flex justify-between gap-4 py-0.5 font-mono text-[10px] text-text-dim"><span>{item.source} <span className="text-text-faint">· {item.sourceType}</span></span><span>{item.timestamp} <span className={CONFIDENCE_COLOR[item.confidence]}>[{item.confidence}]</span></span></div>) : <p className="text-[10px] text-text-faint">No structured evidence supplied.</p>}</section>;
}
