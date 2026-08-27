export const queryKeys = {
  analysis: {
    all: ["analysis"] as const,
    list: (filters: Readonly<Record<string, unknown>> = {}) => ["analysis", "list", filters] as const,
    detail: (runId: string) => ["analysis", runId] as const,
    specialists: (runId: string) => ["analysis", runId, "specialists"] as const,
    bullBear: (runId: string) => ["analysis", runId, "bull-bear"] as const,
    conviction: (runId: string) => ["analysis", runId, "conviction"] as const,
    risk: (runId: string) => ["analysis", runId, "risk"] as const,
    recommendation: (runId: string) => ["analysis", runId, "recommendation"] as const,
  },
  portfolio: {
    state: (portfolioCode?: string) => ["portfolio", "state", portfolioCode ?? "latest"] as const,
    risk: (portfolioCode?: string) => ["portfolio", "risk", portfolioCode ?? "latest"] as const,
  },
  system: {
    live: ["system", "live"] as const,
    ready: ["system", "ready"] as const,
    catalysts: (filters: Readonly<Record<string, unknown>> = {}) => ["catalysts", filters] as const,
    alerts: ["alerts"] as const,
  },
  performance: ["performance"] as const,
} as const;
