"use client";

import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";

export type UseLocalStorageResult<T> = readonly [
  T,
  Dispatch<SetStateAction<T>>,
  () => void,
];

function resolveInitialValue<T>(initialValue: T | (() => T)): T {
  return initialValue instanceof Function ? initialValue() : initialValue;
}

function readStoredValue<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  const rawValue = window.localStorage.getItem(key);
  if (rawValue === null) return fallback;

  try {
    return JSON.parse(rawValue) as T;
  } catch {
    return fallback;
  }
}

export function useLocalStorage<T>(
  key: string,
  initialValue: T | (() => T),
): UseLocalStorageResult<T> {
  const [storedValue, setStoredValue] = useState<T>(() => {
    const fallback = resolveInitialValue(initialValue);
    return readStoredValue(key, fallback);
  });

  const setValue = useCallback<Dispatch<SetStateAction<T>>>(
    (value) => {
      setStoredValue((currentValue) => {
        const nextValue = value instanceof Function ? value(currentValue) : value;
        window.localStorage.setItem(key, JSON.stringify(nextValue));
        return nextValue;
      });
    },
    [key],
  );

  const removeValue = useCallback(() => {
    window.localStorage.removeItem(key);
    setStoredValue(resolveInitialValue(initialValue));
  }, [initialValue, key]);

  useEffect(() => {
    const handleStorage = (event: StorageEvent) => {
      if (event.storageArea !== window.localStorage || event.key !== key) return;
      const fallback = resolveInitialValue(initialValue);
      setStoredValue(event.newValue === null ? fallback : readStoredValue(key, fallback));
    };

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [initialValue, key]);

  return [storedValue, setValue, removeValue] as const;
}
