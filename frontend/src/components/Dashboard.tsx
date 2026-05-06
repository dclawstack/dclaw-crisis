"use client";

import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface CrisisPlan {
  id: string;
  scenario: string;
  severity_level: string;
  response_team: string[];
  communication_channels: string[];
  eta_resolution_hours: number;
  created_at: string
}

export default function Dashboard() {
  const [scenario, setScenario] = useState("");
  const [crisisPlan, setCrisisPlan] = useState<CrisisPlan | null>(null);
  const [extraData, setExtraData] = useState<any>(null);
const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    if (!scenario) return;
    setLoading(true);
    try {
      const res = await fetch("/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
        scenario: scenario,
        }),
      });
      const data = await res.json();
      setCrisisPlan(data);
      const extraRes = await fetch(`/plans/${plan_id}/actions`);
      const extraData = await extraRes.json();
      setExtraData(extraData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div className="flex items-center gap-3">
        <AlertTriangle className="w-8 h-8" style={{ color: "#EA580C" }} />
        <div>
          <h1 className="text-2xl font-bold">DClaw Crisis</h1>
          <p className="text-sm text-slate-500">Crisis response planning</p>
        </div>
        <Badge className="ml-auto" style={{ backgroundColor: "#EA580C" }}>Operations</Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Generate Response Plan</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Crisis scenario</label>
              <Input value={scenario} onChange={(e) => setScenario(e.target.value)} placeholder="e.g. Data center outage" />
            </div>

          </div>
          <Button onClick={handleSubmit} disabled={loading || !scenario}>
            {loading ? "Processing..." : "Generate Response Plan"}
          </Button>
        </CardContent>
      </Card>

      {crisisPlan && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          <Card>
            <CardHeader>
              <CardTitle>Plan Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p><strong>ID:</strong> {plan.id}</p>
              <p><strong>Scenario:</strong> {plan.scenario}</p>
              <p><strong>Severity:</strong> {plan.severity_level}</p>
              <p><strong>ETA Resolution:</strong> {plan.eta_resolution_hours + ' hours'}</p>
              <p><strong>Created:</strong> {new Date(plan.created_at).toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Response Team</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {plan.response_team.map((item: string, i: number) => (
                  <Badge key={i} variant="secondary">{item}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Communication Channels</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {plan.communication_channels.map((item: string, i: number) => (
                  <Badge key={i} variant="secondary">{item}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Response Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {extraData?.map((rec: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                    <span className="text-sm">Step {rec.step}: {rec.action}</span>
                    <Badge variant="secondary">{rec.step}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
