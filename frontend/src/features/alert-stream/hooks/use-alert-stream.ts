"use client";

import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { AuditAction } from "@/entities/audit";
import type { AlertSseEventType, ExitTriggerEventData, RegimeChangeEventData } from "@/entities/system";
import { parseSseJson, queryKeys, SSE_ENDPOINTS } from "@/shared/api";
import { useAuthenticatedSseUrl, useEventSource } from "@/shared/hooks";
import { useAuditStore, useAuthStore } from "@/stores";

const ALERT_SSE_EVENT_TYPES: readonly AlertSseEventType[] = ["regime_change", "exit_trigger"];

export function useAlertStream() {
  const queryClient = useQueryClient();
  const authenticated = useAuthStore((state) => state.status === "authenticated");
  const url = useAuthenticatedSseUrl(SSE_ENDPOINTS.ALERTS_STREAM, authenticated);

  const onMessage = useCallback((event: MessageEvent<string>) => {
    const eventType = event.type as AlertSseEventType;
    if (eventType === "regime_change") {
      const payload = parseSseJson<RegimeChangeEventData>(event);
      if (!payload?.regime || !payload.previous) return;
      toast.warning(`Regime changed to ${payload.regime}`, { description: `Previous regime: ${payload.previous}` });
      useAuditStore.getState().addEntry({
        actor_label: "SYSTEM · SSE",
        action: AuditAction.UPDATE,
        summary: `Market regime changed from ${payload.previous} to ${payload.regime}`,
        reference: "FR-056",
        occurred_at: payload.detected_at,
        sync_status: "synced",
      });
    } else if (eventType === "exit_trigger") {
      const payload = parseSseJson<ExitTriggerEventData>(event);
      if (!payload?.ticker || !payload.trigger || !Number.isFinite(payload.price)) return;
      toast.error(`Exit trigger: ${payload.ticker}`, { description: `${payload.trigger} at ${payload.price}` });
      useAuditStore.getState().addEntry({
        actor_label: "SYSTEM · SSE",
        action: AuditAction.EXECUTE,
        summary: `${payload.ticker} exit trigger ${payload.trigger} fired at ${payload.price}`,
        reference: "FR-055",
        occurred_at: payload.detected_at,
        sync_status: "synced",
      });
    } else {
      return;
    }
    void queryClient.invalidateQueries({ queryKey: queryKeys.system.alerts });
  }, [queryClient]);

  return useEventSource(url, { onMessage, eventTypes: ALERT_SSE_EVENT_TYPES, withCredentials: true });
}
