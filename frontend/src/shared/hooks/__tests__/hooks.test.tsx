import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useClock } from "@/shared/hooks/use-clock";
import { useKeyboardShortcut } from "@/shared/hooks/use-keyboard-shortcut";
import { useLocalStorage } from "@/shared/hooks/use-local-storage";

describe("shared hooks", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("persists typed local storage values and removes them", () => {
    const { result } = renderHook(() => useLocalStorage("terminal-preference", { compact: false }));

    act(() => result.current[1]({ compact: true }));
    expect(result.current[0]).toEqual({ compact: true });
    expect(window.localStorage.getItem("terminal-preference")).toBe('{"compact":true}');

    act(() => result.current[2]());
    expect(result.current[0]).toEqual({ compact: false });
    expect(window.localStorage.getItem("terminal-preference")).toBeNull();
  });

  it("supports lazy defaults, functional updates, malformed storage, and cross-tab changes", () => {
    window.localStorage.setItem("terminal-density", "invalid-json");
    const { result } = renderHook(() => useLocalStorage("terminal-density", () => 1));
    expect(result.current[0]).toBe(1);

    act(() => result.current[1]((current) => current + 1));
    expect(result.current[0]).toBe(2);

    act(() => {
      window.localStorage.setItem("terminal-density", "3");
      window.dispatchEvent(new StorageEvent("storage", {
        key: "terminal-density",
        newValue: "3",
        storageArea: window.localStorage,
      }));
    });
    expect(result.current[0]).toBe(3);
  });

  it("runs matching keyboard shortcuts outside editable controls", () => {
    const callback = vi.fn();
    renderHook(() => useKeyboardShortcut("k", callback, { ctrl: true }));

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true }));
    expect(callback).toHaveBeenCalledOnce();

    const input = document.createElement("input");
    document.body.append(input);
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true }));
    expect(callback).toHaveBeenCalledOnce();
    input.remove();
  });

  it("advances the clock on the configured interval", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-08-26T00:00:00.000Z"));
    const { result } = renderHook(() => useClock(1_000));

    act(() => {
      vi.advanceTimersByTime(1_000);
    });

    expect(result.current.toISOString()).toBe("2026-08-26T00:00:01.000Z");
    vi.useRealTimers();
  });
});
