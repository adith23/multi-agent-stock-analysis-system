const DEFAULT_LOCALE = "en-US";

export interface NumberFormatOptions extends Intl.NumberFormatOptions {
  locale?: string;
}

export function formatNumber(value: number, options: NumberFormatOptions = {}): string {
  const { locale = DEFAULT_LOCALE, ...formatOptions } = options;
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: 2,
    ...formatOptions,
  }).format(value);
}

export function formatCurrency(
  value: number | string,
  currency = "USD",
  options: NumberFormatOptions = {},
): string {
  const numericValue = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(numericValue)) {
    return "—";
  }

  return formatNumber(numericValue, {
    style: "currency",
    currency,
    currencyDisplay: "narrowSymbol",
    ...options,
  });
}

export function formatPercentage(
  value: number,
  options: NumberFormatOptions & { input?: "decimal" | "percent" } = {},
): string {
  const { input = "decimal", ...formatOptions } = options;
  const normalizedValue = input === "percent" ? value / 100 : value;
  return formatNumber(normalizedValue, {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
    ...formatOptions,
  });
}
