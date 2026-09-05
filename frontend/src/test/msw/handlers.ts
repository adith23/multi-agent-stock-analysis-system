import { http, HttpResponse } from "msw";

import { UserRole } from "@/entities/user";
import { publicEnvironment } from "@/shared/config/public-env";

export const API_URL = `${publicEnvironment.apiBaseUrl.replace(/\/$/, "")}/*`;

export const defaultHandlers = [
  http.post(`${publicEnvironment.apiBaseUrl}/auth/token/`, () => HttpResponse.json({ access: "test-access", refresh: "test-refresh" })),
  http.get(`${publicEnvironment.apiBaseUrl}/auth/me/`, () => HttpResponse.json({
    id: "user-1",
    username: "pm.test",
    email: "pm@example.com",
    first_name: "Test",
    last_name: "Manager",
    job_title: "Portfolio Manager",
    role: UserRole.PORTFOLIO_MANAGER,
  })),
];
