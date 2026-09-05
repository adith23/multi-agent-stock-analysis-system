import type { StressScenarioView } from "../types/risk-compliance.types";

export function StressTestTable({ scenarios }: { scenarios: readonly StressScenarioView[] }) { return <div role="table" aria-label="Stress test scenarios">{scenarios.map((scenario) => <div key={scenario.scenario} role="row" className="flex justify-between border-b border-hairline py-2 font-mono text-xs last:border-0"><span role="cell" className="text-text-dim">{scenario.scenario}</span><span role="cell" className="text-red">{scenario.impact}</span></div>)}</div>; }
