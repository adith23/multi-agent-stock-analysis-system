import type { JsonObject } from "@/shared/types";

export enum AuditAction {
  CREATE = "create",
  READ = "read",
  UPDATE = "update",
  DELETE = "delete",
  LOGIN = "login",
  LOGOUT = "logout",
  APPROVE = "approve",
  REJECT = "reject",
  OVERRIDE = "override",
  ESCALATE = "escalate",
  EXECUTE = "execute",
  REQUEST = "request",
  ERROR = "error",
}

export interface AuditTrailRecord {
  id: string;
  occurred_at: string;
  actor: string | null;
  actor_label: string;
  action: AuditAction;
  event_type: string;
  resource_type: string;
  resource_id: string;
  request_id: string;
  method: string;
  path: string;
  status_code: number | null;
  ip_address: string | null;
  user_agent: string;
  summary: string;
  metadata: JsonObject;
  previous_values: JsonObject;
  new_values: JsonObject;
  agent_version: string;
  model_version: string;
  prompt_version: string;
  event_hash: string;
}

export interface AuditEntry {
  id: string;
  occurred_at: string;
  actor_label: string;
  action: AuditAction;
  summary: string;
  reference: string;
  sync_status: "pending" | "synced" | "failed";
}
