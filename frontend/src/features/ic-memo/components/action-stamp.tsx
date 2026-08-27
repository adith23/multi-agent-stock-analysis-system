import { ActionSignal } from "@/entities/recommendation";
import { cn } from "@/shared/lib";

const POSITIVE = new Set([ActionSignal.STRONG_BUY, ActionSignal.BUY, ActionSignal.ACCUMULATE]);
const NEGATIVE = new Set([ActionSignal.REDUCE, ActionSignal.SELL, ActionSignal.STRONG_SELL]);

export function ActionStamp({ action, conviction }: { action: ActionSignal; conviction: number }) {
  const color = POSITIVE.has(action) ? "border-green text-green" : NEGATIVE.has(action) ? "border-red text-red" : "border-amber text-amber";
  return <div className={cn("absolute top-14 right-5 grid size-24 -rotate-8 place-content-center rounded-full border-[3px] border-double text-center opacity-90 motion-safe:animate-[stamp-in_.5s_cubic-bezier(.2,.8,.3,1.2)]", color)} aria-label={`${action.replaceAll("_", " ")}, conviction ${conviction}`}><strong className="font-mono text-xs tracking-wide uppercase">{action.replaceAll("_", " ")}</strong><span className="mt-1 font-mono text-[9px]">CONV {conviction}</span></div>;
}
