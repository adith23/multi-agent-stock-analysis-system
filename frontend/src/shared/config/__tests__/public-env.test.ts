import { describe, expect, it } from "vitest";

import { assertProductionPublicEnvironment, parsePublicEnvironment } from "../public-env";

describe("public environment", () => {
  it("normalizes configured HTTP endpoints and applies the API fallback to SSE", () => {
    expect(parsePublicEnvironment("https://api.example.com/v1/")).toEqual({
      apiBaseUrl: "https://api.example.com/v1",
      sseBaseUrl: "https://api.example.com/v1",
    });
  });

  it("rejects malformed, non-HTTP, and credential-bearing production URLs", () => {
    expect(() => parsePublicEnvironment("not-a-url")).toThrow(/absolute HTTP/i);
    expect(() => parsePublicEnvironment("file:///tmp/api")).toThrow(/http or https/i);
    expect(() => assertProductionPublicEnvironment({
      apiBaseUrl: "https://user:secret@api.example.com/v1",
      sseBaseUrl: "https://api.example.com/v1",
    }, "production")).toThrow(/credentials/i);
    expect(() => assertProductionPublicEnvironment({
      apiBaseUrl: "https://user:secret@api.example.com/v1",
      sseBaseUrl: "https://api.example.com/v1",
    }, "development")).not.toThrow();
  });
});
