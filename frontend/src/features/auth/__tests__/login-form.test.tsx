import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/features/auth/components/login-form";

vi.mock("@/features/auth/hooks/use-auth", () => ({
  useLogin: () => ({ mutate: vi.fn(), isPending: false, isError: false, error: null }),
}));

describe("LoginForm", () => {
  it("requires both institutional credentials before submission", () => {
    const client = new QueryClient();
    render(<QueryClientProvider client={client}><LoginForm /></QueryClientProvider>);

    const submit = screen.getByRole("button", { name: "Enter terminal" });
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "analyst" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secure-password" } });
    expect(submit).toBeEnabled();
  });
});
