import { CheckCircle2, XCircle } from "lucide-react";
import type { ComplianceCheckView } from "../types/risk-compliance.types";

export function ComplianceChecklist({ checks }: { checks: readonly ComplianceCheckView[] }) { return <ul>{checks.map((check) => <li key={check.label} className="flex items-center gap-2 py-1 text-xs">{check.pass ? <CheckCircle2 className="size-3.5 text-green" aria-hidden="true" /> : <XCircle className="size-3.5 text-red" aria-hidden="true" />}{check.label}</li>)}</ul>; }
