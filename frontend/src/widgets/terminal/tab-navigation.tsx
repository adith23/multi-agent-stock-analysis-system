import { cn } from "@/shared/lib";
import { useTerminalStore, type TerminalTab } from "@/stores/terminal-store";

const TABS: readonly { id: TerminalTab; label: string; shortLabel: string }[] = [
  { id: "overview", label: "Investment committee memo", shortLabel: "IC Memo" },
  { id: "specialists", label: "Specialist reports", shortLabel: "Specialist Reports" },
  { id: "adversarial", label: "Adversarial review", shortLabel: "Bull vs. Bear" },
  { id: "risk", label: "Risk and compliance", shortLabel: "Risk + Compliance" },
  { id: "analytics", label: "Advanced analytics", shortLabel: "Analytics" },
  { id: "audit", label: "Audit trail", shortLabel: "Audit" },
];

export function TabNavigation() {
  const activeTab = useTerminalStore((state) => state.activeTab);
  const setActiveTab = useTerminalStore((state) => state.setActiveTab);

  return (
    <nav className="h-9 shrink-0 border-b border-hairline bg-panel" aria-label="Analysis workspace">
      <div className="flex h-full items-stretch px-2" role="tablist" aria-label="Terminal views">
        {TABS.map((tab) => {
          const active = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={active}
              aria-controls={`terminal-panel-${tab.id}`}
              id={`terminal-tab-${tab.id}`}
              className={cn(
                "relative px-3 font-mono text-[9px] tracking-[0.06em] uppercase outline-none transition-colors hover:text-text-primary focus-visible:bg-amber/5 focus-visible:text-amber",
                active ? "text-amber after:absolute after:inset-x-2 after:bottom-0 after:h-px after:bg-amber" : "text-text-faint",
              )}
              onClick={() => setActiveTab(tab.id)}
              title={tab.label}
            >
              {tab.shortLabel}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
