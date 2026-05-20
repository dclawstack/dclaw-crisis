"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, ShieldCheck } from "lucide-react";

import { signin } from "@/lib/api";
import { setSession } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function SigninForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    setError(null);
    try {
      const res = await signin({
        email: String(f.get("email")),
        password: String(f.get("password")),
      });
      setSession(res.token.access_token, res.user);
      const next = params.get("next") || "/dashboard";
      router.replace(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label>Email</Label>
        <Input name="email" type="email" autoComplete="email" required />
      </div>
      <div>
        <Label>Password</Label>
        <Input name="password" type="password" autoComplete="current-password" required minLength={8} />
      </div>
      {error && <div className="text-xs bg-red-50 border border-red-200 text-red-700 rounded p-2">{error}</div>}
      <Button type="submit" className="w-full" disabled={busy}>
        {busy ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : null}
        Sign in
      </Button>
    </form>
  );
}

export default function SigninPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 via-white to-rose-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto h-10 w-10 rounded-full bg-pink-600 text-white flex items-center justify-center mb-2">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <CardTitle>Sign in to DClaw Crisis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Suspense fallback={<div className="text-sm text-slate-500">Loading…</div>}>
            <SigninForm />
          </Suspense>
          <div className="text-xs text-center text-slate-500">
            New here? <Link href="/signup" className="text-pink-700 hover:underline">Create an account</Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
