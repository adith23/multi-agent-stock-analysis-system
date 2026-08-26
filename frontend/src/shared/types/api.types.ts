export type JsonPrimitive = boolean | number | string | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonValue[];
export type JsonObject = { [key: string]: JsonValue };
export type DecimalString = string;

export interface ApiEntity {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface VersionedApiEntity extends ApiEntity {
  version: number;
  agent_version: string;
  model_version: string;
  prompt_version: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiFieldErrors {
  [field: string]: string | string[] | ApiFieldErrors;
}

export interface ApiErrorResponse {
  detail?: string;
  code?: string;
  errors?: ApiFieldErrors;
}
