"use client";

import { useEffect, useState } from "react";

const TOKEN_KEY = "dclaw-crisis-token";
const USER_KEY = "dclaw-crisis-user";

export interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  auth_provider: string;
  is_active: boolean;
  is_admin: boolean;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw) as AuthUser; } catch { return null; }
}

export function setSession(token: string, user: AuthUser) {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.dispatchEvent(new CustomEvent("dclaw-auth-changed"));
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new CustomEvent("dclaw-auth-changed"));
}

/** React hook returning the current user (or null) with live updates. */
export function useAuth(): { user: AuthUser | null; token: string | null; loading: boolean } {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    function refresh() {
      setUser(getUser());
      setToken(getToken());
      setLoading(false);
    }
    refresh();
    window.addEventListener("dclaw-auth-changed", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("dclaw-auth-changed", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  return { user, token, loading };
}
