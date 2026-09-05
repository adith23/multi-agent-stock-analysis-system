import { AlertTriangle, ArrowDownRight, ArrowUpRight, XCircle } from "lucide-react";
import type { JsonValue } from "@/shared/types";
import { Chip, DataModeBadge, FeatureError, FeatureLoading, Panel, SectionLabel } from "@/shared/ui";
import { useTerminalStore } from "@/stores/terminal-store";
import { useBullBear } from "../hooks/use-bull-bear";
import { MOCK_BULL_BEAR } from "../model/mock-bull-bear";
import type { BullBearMemoView } from "../types/bull-bear.types";

function strings(values: JsonValue[]): string[] { return values.map((value) => typeof value === "string" ? value : JSON.stringify(value)); }
const list = (items: readonly string[]) => <ul className="list-disc space-y-2 pl-5 text-xs leading-relaxed text-text-dim">{items.map((item) => <li key={item}>{item}</li>)}</ul>;

export function BullBearPanel() {
  const runId = useTerminalStore((state) => state.activeRunId);
  const query = useBullBear(runId);
  if (query.isLoading) return <FeatureLoading label="adversarial review" />;
  if (query.isError) return <FeatureError error={query.error} retry={() => void query.refetch()} />;
  const remote = Boolean(query.data);
  const memo: BullBearMemoView = query.data ? { bullArguments: [query.data.bull_case], bearArguments: [query.data.bear_case], weakAssumptions: strings(query.data.weak_assumptions), preMortem: strings(query.data.premortem), materialUnknowns: strings(query.data.material_unknowns), roundsCompleted: query.data.debate_rounds } : MOCK_BULL_BEAR;
  return <div className="max-w-[900px]"><div className="mb-3 flex items-center justify-between"><h2 className="font-serif text-lg font-semibold">Adversarial Decision Memo</h2><div className="flex items-center gap-2"><Chip>{memo.roundsCompleted} debate rounds</Chip><DataModeBadge remote={remote} refreshing={query.isFetching} /></div></div><div className="mb-3 grid grid-cols-2 gap-3"><Panel borderColor="color-mix(in srgb, var(--color-green) 40%, transparent)"><SectionLabel icon={ArrowUpRight}>Bull case</SectionLabel>{list(memo.bullArguments)}</Panel><Panel borderColor="color-mix(in srgb, var(--color-red) 40%, transparent)"><SectionLabel icon={ArrowDownRight}>Bear case</SectionLabel>{list(memo.bearArguments)}</Panel></div><Panel className="mb-3"><SectionLabel icon={AlertTriangle}>Weak assumptions &amp; contradictions</SectionLabel>{list(memo.weakAssumptions)}</Panel><Panel className="mb-3"><SectionLabel icon={XCircle}>Pre-mortem — conditions for failure</SectionLabel>{list(memo.preMortem)}</Panel><Panel><SectionLabel>Material unknowns</SectionLabel><div className="flex flex-wrap gap-2">{memo.materialUnknowns.map((unknown) => <Chip key={unknown}>{unknown}</Chip>)}</div></Panel></div>;
}
