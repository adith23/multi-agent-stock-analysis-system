"use client";

import { useState, type FormEvent } from "react";
import { KeyRound, LoaderCircle, UserRound } from "lucide-react";

import { ApiError } from "@/shared/api";
import { ActionButton, Panel } from "@/shared/ui";
import { Input } from "@/shared/ui/shadcn";

import { useLogin } from "../hooks/use-auth";

export function LoginForm() {
  const login = useLogin();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!username.trim() || !password) return;
    login.mutate({ username: username.trim(), password });
  }

  const detail = login.error instanceof ApiError ? login.error.message : null;

  return (
    <Panel className="w-full max-w-[420px] border-amber/25 p-6" aria-labelledby="login-heading">
      <div className="mb-6 border-b border-hairline pb-4">
        <p className="font-mono text-[9px] tracking-[0.18em] text-amber uppercase">Secure terminal access</p>
        <h1 id="login-heading" className="mt-2 font-serif text-2xl font-semibold">Authenticate to Conclave</h1>
        <p className="mt-2 text-xs leading-5 text-text-dim">Your institutional role and permitted actions are loaded from the authenticated backend identity.</p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit} noValidate>
        <label className="block">
          <span className="mb-1.5 flex items-center gap-1.5 font-mono text-[9px] tracking-[0.1em] text-text-faint uppercase"><UserRound className="size-3" /> Username</span>
          <Input name="username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} disabled={login.isPending} required />
        </label>
        <label className="block">
          <span className="mb-1.5 flex items-center gap-1.5 font-mono text-[9px] tracking-[0.1em] text-text-faint uppercase"><KeyRound className="size-3" /> Password</span>
          <Input name="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} disabled={login.isPending} required />
        </label>
        {login.isError ? <p role="alert" className="rounded-terminal border border-red/30 bg-red/10 p-2.5 text-xs text-red">{detail ?? "Unable to authenticate."}</p> : null}
        <ActionButton type="submit" className="w-full" disabled={login.isPending || !username.trim() || !password}>
          {login.isPending ? <><LoaderCircle className="mr-2 size-3.5 animate-spin" /> Authenticating</> : "Enter terminal"}
        </ActionButton>
      </form>
    </Panel>
  );
}
