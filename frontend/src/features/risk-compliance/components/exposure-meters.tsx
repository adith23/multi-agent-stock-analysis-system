import { Meter } from "@/shared/ui";
import type { ExposureMetricView } from "../types/risk-compliance.types";

export function ExposureMeters({ exposures }: { exposures: readonly ExposureMetricView[] }) { return <div className="grid grid-cols-2 gap-4">{exposures.map((exposure) => <div key={exposure.label}><div className="mb-1 flex justify-between font-mono text-[10px]"><span>{exposure.label}</span><span className="text-text-dim">{exposure.value} / {exposure.limit}</span></div><Meter value={exposure.value} limit={exposure.limit} /></div>)}</div>; }
