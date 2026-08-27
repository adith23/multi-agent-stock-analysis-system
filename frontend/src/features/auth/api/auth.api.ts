import type { LoginRequest, LogoutRequest, TokenPair, User } from "@/entities/user";
import { apiClient, ENDPOINTS } from "@/shared/api";

export const authApi = {
  async login(credentials: LoginRequest): Promise<TokenPair> {
    return (await apiClient.post<TokenPair>(ENDPOINTS.AUTH_TOKEN, credentials)).data;
  },
  async me(): Promise<User> {
    return (await apiClient.get<User>(ENDPOINTS.AUTH_ME)).data;
  },
  async logout(payload: LogoutRequest): Promise<void> {
    await apiClient.post(ENDPOINTS.AUTH_LOGOUT, payload);
  },
};
