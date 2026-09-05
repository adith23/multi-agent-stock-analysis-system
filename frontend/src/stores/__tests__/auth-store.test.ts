import { describe, expect, it } from "vitest";

import { UserRole, type User } from "@/entities/user";
import { useAuthStore } from "@/stores/auth-store";
import { useTerminalStore } from "@/stores/terminal-store";

const user: User = {
  id: "9ca3c21b-85ad-4edf-962d-b51a7a39ded1",
  username: "risk.lead",
  email: "risk@example.com",
  first_name: "Risk",
  last_name: "Lead",
  job_title: "Chief Risk Officer",
  role: UserRole.RISK_OFFICER,
};

describe("auth store", () => {
  it("makes the authenticated backend role authoritative for terminal actions", () => {
    useTerminalStore.getState().resetTerminal();
    useAuthStore.getState().setAuthenticated(user);

    expect(useAuthStore.getState()).toMatchObject({ status: "authenticated", user });
    expect(useTerminalStore.getState().role).toBe(UserRole.RISK_OFFICER);

    useAuthStore.getState().setUnauthenticated();
    expect(useAuthStore.getState().user).toBeNull();
    expect(useTerminalStore.getState().role).toBe(UserRole.RESEARCH_ANALYST);
  });
});
