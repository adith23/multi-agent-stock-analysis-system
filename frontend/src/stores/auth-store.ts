import { create } from "zustand";

import type { User } from "@/entities/user";
import { UserRole } from "@/entities/user";

import { useTerminalStore } from "./terminal-store";

export type AuthStatus = "checking" | "authenticated" | "unauthenticated";

interface AuthState {
  status: AuthStatus;
  user: User | null;
  setAuthenticated: (user: User) => void;
  setUnauthenticated: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  status: "checking",
  user: null,
  setAuthenticated: (user) => {
    useTerminalStore.getState().setRole(user.role);
    set({ status: "authenticated", user });
  },
  setUnauthenticated: () => {
    useTerminalStore.getState().setRole(UserRole.RESEARCH_ANALYST);
    set({ status: "unauthenticated", user: null });
  },
}));
