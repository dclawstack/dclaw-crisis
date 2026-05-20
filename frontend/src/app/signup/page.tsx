"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, UserPlus } from "lucide-react";

import { signup } from "@/lib/api";
import { setSession } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function SignupPage() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    setError(null);
    try {
      const res = await signup({
        email: String(f.get("email")),
        password: String(f.get("password")),
        name: String(f.get("name") || "") || undefined,
      });
      setSession(res.token.access_token, res.user);
      router.replace("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-up failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 via-white to-rose-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto h-10 w-10 rounded-full bg-pink-600 text-white flex items-center justify-center mb-2">
            <UserPlus className="h-5 w-5" />
          </div>
          <CardTitle>Create your account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Name (optional)</Label>
              <Input name="name" autoComplete="name" />
            </div>
            <div>
              <Label>Email</Label>
              <Input name="email" type="email" autoComplete="email" required />
            </div>
            <div>
              <Label>Password</Label>
              <Input name="password" type="password" autoComplete="new-password" required minLength={8} />
              <p className="text-[11px] text-slate-500 mt-1">At least 8 characters.</p>
            </div>
            {error && <div className="text-xs bg-red-50 border border-red-200 text-red-700 rounded p-2">{error}</div>}
            <Button type="submit" className="w-full" disabled={busy}>
              {busy ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : null}
              Create account
            </Button>
          </form>
          <div className="text-xs text-center text-slate-500">
            Already have an account? <Link href="/signin" className="text-pink-700 hover:underline">Sign in</Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
