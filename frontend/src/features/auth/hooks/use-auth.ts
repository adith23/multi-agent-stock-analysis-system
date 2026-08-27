"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import type { LoginRequest } from "@/entities/user";
import { clearAuthTokens, getRefreshToken, storeAuthTokens } from "@/shared/api";
import { useAuthStore } from "@/stores";

import { authApi } from "../api/auth.api";

export function useLogin() {
  const router = useRouter();
  const setAuthenticated = useAuthStore((state) => state.setAuthenticated);

  return useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const tokens = await authApi.login(credentials);
      storeAuthTokens(tokens);
      try {
        const user = await authApi.me();
        return { tokens, user };
      } catch (error) {
        clearAuthTokens();
        throw error;
      }
    },
    onSuccess: ({ user }) => {
      setAuthenticated(user);
      router.replace("/");
      router.refresh();
    },
    onError: () => toast.error("Sign-in failed. Check your credentials and try again."),
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const setUnauthenticated = useAuthStore((state) => state.setUnauthenticated);

  return useMutation({
    mutationFn: async () => {
      const refresh = getRefreshToken();
      if (refresh) await authApi.logout({ refresh });
    },
    onSettled: () => {
      clearAuthTokens();
      queryClient.clear();
      setUnauthenticated();
      router.replace("/login");
      router.refresh();
    },
  });
}
