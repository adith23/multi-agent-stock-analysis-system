import { type FormEvent, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { ActionButton } from "@/shared/ui";
import { Input } from "@/shared/ui/shadcn";
import { useTerminalStore } from "@/stores/terminal-store";

const TICKER_PATTERN = /^[A-Z][A-Z0-9.-]{0,9}$/;

export interface TickerSearchBarProps {
  onSubmit: (ticker: string) => void;
  isSubmitting?: boolean;
}

export function TickerSearchBar({ onSubmit, isSubmitting = false }: TickerSearchBarProps) {
  const tickerInput = useTerminalStore((state) => state.tickerInput);
  const setTickerInput = useTerminalStore((state) => state.setTickerInput);
  const systemState = useTerminalStore((state) => state.systemState);
  const [submitted, setSubmitted] = useState(false);
  const normalizedTicker = tickerInput.trim().toUpperCase();
  const isValid = useMemo(() => TICKER_PATTERN.test(normalizedTicker), [normalizedTicker]);
  const errorId = "ticker-search-error";

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitted(true);
    if (!isValid || systemState === "running" || isSubmitting) return;
    onSubmit(normalizedTicker);
  }

  return (
    <form className="flex items-center gap-1.5" onSubmit={handleSubmit} noValidate>
      <label className="sr-only" htmlFor="ticker-search-input">Ticker symbol</label>
      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-text-faint" aria-hidden="true" />
        <Input
          id="ticker-search-input"
          className="h-8 w-32 pl-8 text-[12px] tracking-[0.08em]"
          value={tickerInput}
          maxLength={10}
          placeholder="HLXD"
          autoComplete="off"
          spellCheck={false}
          aria-invalid={submitted && !isValid}
          aria-describedby={submitted && !isValid ? errorId : undefined}
          onChange={(event) => {
            setSubmitted(false);
            setTickerInput(event.target.value.replace(/\s/g, ""));
          }}
        />
        {submitted && !isValid ? (
          <span id={errorId} role="alert" className="sr-only">
            Enter a valid ticker using up to 10 letters, numbers, periods, or hyphens.
          </span>
        ) : null}
      </div>
      <ActionButton className="h-8 min-h-8 px-3" type="submit" disabled={!isValid || systemState === "running" || isSubmitting}>
        {isSubmitting ? "Queuing" : systemState === "running" ? "Running" : "Go"}
      </ActionButton>
    </form>
  );
}
