import { ShieldCheck } from "lucide-react";
import { StanceIcon } from "@/shared/ui";
import type { SignalAgreementView } from "../types/ic-memo.types";

export function SignalAgreementMatrix({ agreement }: { agreement: readonly SignalAgreementView[] }) {
  return <div className="flex flex-wrap gap-x-5 gap-y-2 font-mono text-[11px]">{agreement.length ? agreement.map((item) => <span key={item.agent} className="flex items-center gap-1"><StanceIcon stance={item.stance} />{item.agent}</span>) : <span className="text-text-faint">Agreement matrix not available</span>}<span className="flex items-center gap-1"><ShieldCheck className="size-3.5 text-green" aria-hidden="true" />Risk gate available separately</span></div>;
}
