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
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    let nextIndex: number | null = null;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % TABS.length;
    if (event.key === "ArrowLeft") nextIndex = (index - 1 + TABS.length) % TABS.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = TABS.length - 1;
    if (nextIndex === null) return;

    event.preventDefault();
    const nextTab = TABS[nextIndex];
    setActiveTab(nextTab.id);
    tabRefs.current[nextIndex]?.focus();
  }

  return (
    <nav className="h-9 shrink-0 border-b border-hairline bg-panel" aria-label="Analysis workspace">
      <div className="flex h-full items-stretch px-10" role="tablist" aria-label="Terminal views">
        {TABS.map((tab, index) => {
          const active = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              ref={(element) => { tabRefs.current[index] = element; }}
              type="button"
              role="tab"
              aria-selected={active}
              aria-controls={`terminal-panel-${tab.id}`}
              aria-keyshortcuts={`${index + 1}`}
              id={`terminal-tab-${tab.id}`}
              tabIndex={active ? 0 : -1}
              className={cn(
                "relative px-3 font-mono text-[9px] tracking-[0.06em] uppercase outline-none transition-colors hover:text-text-primary focus-visible:bg-amber/5 focus-visible:text-amber",
                active ? "text-amber after:absolute after:inset-x-2 after:bottom-0 after:h-px after:bg-amber" : "text-text-faint",
              )}
              onClick={() => setActiveTab(tab.id)}
              onKeyDown={(event) => handleKeyDown(event, index)}
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
import { type KeyboardEvent, useRef } from "react";
