const STATUS_ITEMS = [
  "AGENTS: macro-v1 · fundamental-v1 · technical-v1 · sentiment-v1",
  "AUDIT: append-only event model",
  "DATA ISOLATION: portfolio scoped",
  "RETENTION: 400 days",
  "STREAMING: SSE connection monitored",
  "MODE: API + typed fixtures",
] as const;

const tickerText = STATUS_ITEMS.join("   ◆   ");

export function StatusTicker() {
  return (
    <footer role="contentinfo" className="flex h-terminal-footer shrink-0 items-center overflow-hidden border-t border-hairline bg-inset font-mono text-[8px] tracking-[0.1em] text-text-faint uppercase" aria-label="Terminal status">
      <span className="shrink-0 border-r border-hairline bg-panel px-3 py-1 text-amber">System status</span>
      <div className="group min-w-0 flex-1 overflow-hidden">
        <div className="flex w-max animate-marquee whitespace-nowrap group-hover:[animation-play-state:paused]">
          <span className="px-6">{tickerText}</span>
          <span className="px-6" aria-hidden="true">{tickerText}</span>
        </div>
      </div>
    </footer>
  );
}
