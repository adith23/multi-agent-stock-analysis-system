"use client";

import type { RefObject } from "react";

import { useKeyboardShortcut } from "@/shared/hooks";
import { useTerminalStore, type TerminalTab } from "@/stores/terminal-store";

const NUMBERED_TABS: readonly TerminalTab[] = [
  "overview",
  "specialists",
  "adversarial",
  "risk",
  "analytics",
  "audit",
];

export function useTerminalKeyboardShortcuts(searchInputRef: RefObject<HTMLInputElement | null>): void {
  const focusSearch = () => {
    searchInputRef.current?.focus();
    searchInputRef.current?.select();
  };

  useKeyboardShortcut("k", focusSearch, { ctrl: true });
  useKeyboardShortcut("k", focusSearch, { meta: true });
  useKeyboardShortcut("/", focusSearch);
  useKeyboardShortcut("1", () => useTerminalStore.getState().setActiveTab(NUMBERED_TABS[0]));
  useKeyboardShortcut("2", () => useTerminalStore.getState().setActiveTab(NUMBERED_TABS[1]));
  useKeyboardShortcut("3", () => useTerminalStore.getState().setActiveTab(NUMBERED_TABS[2]));
  useKeyboardShortcut("4", () => useTerminalStore.getState().setActiveTab(NUMBERED_TABS[3]));
  useKeyboardShortcut("5", () => useTerminalStore.getState().setActiveTab(NUMBERED_TABS[4]));
  useKeyboardShortcut("6", () => useTerminalStore.getState().setActiveTab(NUMBERED_TABS[5]));
}
