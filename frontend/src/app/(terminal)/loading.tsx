import { Skeleton } from "@/shared/ui";

export default function TerminalLoading() {
  return (
    <main className="flex h-dvh min-w-[1080px] flex-col overflow-hidden bg-void" aria-label="Loading terminal">
      <Skeleton className="h-terminal-header shrink-0 rounded-none border-b border-hairline" />
      <Skeleton className="h-12 shrink-0 rounded-none border-b border-hairline" />
      <div className="grid min-h-0 flex-1 grid-cols-[226px_minmax(0,1fr)_250px]">
        <Skeleton className="rounded-none border-r border-hairline" />
        <Skeleton className="m-4" />
        <Skeleton className="rounded-none border-l border-hairline" />
      </div>
      <Skeleton className="h-terminal-footer shrink-0 rounded-none border-t border-hairline" />
    </main>
  );
}
