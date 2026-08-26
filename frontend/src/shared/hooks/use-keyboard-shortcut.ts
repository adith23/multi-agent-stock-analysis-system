"use client";

import { useEffect, useRef } from "react";

export interface KeyboardShortcutOptions {
  alt?: boolean;
  ctrl?: boolean;
  enabled?: boolean;
  meta?: boolean;
  preventDefault?: boolean;
  shift?: boolean;
  allowInEditable?: boolean;
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return target.isContentEditable || ["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName);
}

export function useKeyboardShortcut(
  key: string,
  callback: (event: KeyboardEvent) => void,
  options: KeyboardShortcutOptions = {},
): void {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const {
    alt = false,
    ctrl = false,
    enabled = true,
    meta = false,
    preventDefault = true,
    shift = false,
    allowInEditable = false,
  } = options;

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (!allowInEditable && isEditableTarget(event.target)) return;
      if (event.key.toLowerCase() !== key.toLowerCase()) return;
      if (event.altKey !== alt || event.ctrlKey !== ctrl || event.metaKey !== meta || event.shiftKey !== shift) return;

      if (preventDefault) event.preventDefault();
      callbackRef.current(event);
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [allowInEditable, alt, ctrl, enabled, key, meta, preventDefault, shift]);
}
