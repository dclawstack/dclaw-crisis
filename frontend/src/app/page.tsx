"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getDashboard, listCrises, listActionItems, type Crisis, type ActionItem, ApiError } from "@/lib/api";

function severityColor(sev: string) {
  switch (sev) {
    case "critical": return "bg-red-600 text-white";
    case "high": return "bg-orange-500 text-white";
    case "medium": return "bg-yellow-500 text-black";
    default: return "bg-blue-500 text-white";
  }
}

function statusColor(st: string) {
  switch (st) {
    case "resolved": return "bg-green-500 text-white";
    case "contained": return "bg-teal-500 text-white";
    case "responding": return "bg-indigo-500 text-white";
    case "assessing": return "bg-purple-500 text-white";
    default: return "bg-gray-500 text-white";
  }
}

export default function Dashboard() {
  const [stats, setStats] = useState<{
    active_crises: number;
    open_action_items: number;
    critical_crises: number;
    avg_resolution_hours: number;
    severity_breakdown: Record<string, number>;
    status_breakdown: Record<string, number>;
    total_crises: number;
  } | null>(null);
  const [crises, setCrises] = useState<Crisis[]>([]);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [d, c, a] = await Promise.all([
          getDashboard(),
          listCrises(),
          listActionItems(),
        ]);
        setStats(d);
        setCrises(c.slice(0, 5));
        setActions(a.slice(0, 5));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div className="p-8">Loading dashboard...</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">DClaw Crisis</h1>
          <p className="text-sm text-gray-500">AI-native Crisis & Incident Command Center</p>
        </div>
        <div className="flex gap-3">
          <Link href="/crisis"><Button variant="outline">Crises</Button></Link>
          <Link href="/team"><Button variant="outline">Team</Button></Link>
          <Link href="/action-items"><Button variant="outline">Action Items</Button></Link>
          <Link href="/playbooks"><Button variant="outline">Playbooks</Button></Link>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2"><CardDescription>Active Crises</CardDescription></CardHeader>
            <CardContent><div className="text-3xl font-bold">{stats?.active_crises ?? 0}</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardDescription>Open Action Items</CardDescription></CardHeader>
            <CardContent><div className="text-3xl font-bold">{stats?.open_action_items ?? 0}</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardDescription>Critical Crises</CardDescription></CardHeader>
            <CardContent><div className="text-3xl font-bold text-red-600">{stats?.critical_crises ?? 0}</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardDescription>Avg. Resolution (hrs)</CardDescription></CardHeader>
            <CardContent><div className="text-3xl font-bold">{stats?.avg_resolution_hours ?? 0}</div></CardContent>
          </Card>
        </div>

        {/* Charts / Breakdowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader><CardTitle>Crises by Severity</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(stats?.severity_breakdown ?? {}).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className={severityColor(k)}>{k}</Badge>
                      <span className="text-sm text-gray-600 capitalize">{k.replace("_", " ")}</span>
                    </div>
                    <span className="font-semibold">{v}</span>
                  </div>
                ))}
                {Object.keys(stats?.severity_breakdown ?? {}).length === 0 && (
                  <p className="text-sm text-gray-400">No data yet</p>
                )}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Crises by Status</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(stats?.status_breakdown ?? {}).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className={statusColor(k)}>{k}</Badge>
                      <span className="text-sm text-gray-600 capitalize">{k.replace("_", " ")}</span>
                    </div>
                    <span className="font-semibold">{v}</span>
                  </div>
                ))}
                {Object.keys(stats?.status_breakdown ?? {}).length === 0 && (
                  <p className="text-sm text-gray-400">No data yet</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Lists */}
        <Tabs defaultValue="crises">
          <TabsList>
            <TabsTrigger value="crises">Recent Crises</TabsTrigger>
            <TabsTrigger value="actions">Recent Action Items</TabsTrigger>
          </TabsList>
          <TabsContent value="crises">
            <Card>
              <CardContent className="pt-6">
                {crises.length === 0 ? (
                  <p className="text-sm text-gray-400">No crises recorded yet.</p>
                ) : (
                  <div className="space-y-3">
                    {crises.map((c) => (
                      <div key={c.id} className="flex items-center justify-between border-b last:border-0 pb-3 last:pb-0">
                        <div>
                          <Link href={`/crisis/${c.id}`} className="font-medium text-blue-700 hover:underline">
                            {c.title}
                          </Link>
                          <div className="text-xs text-gray-500 mt-0.5">{c.category.replace("_", " ")}</div>
                        </div>
                        <div className="flex gap-2">
                          <Badge className={severityColor(c.severity)}>{c.severity}</Badge>
                          <Badge className={statusColor(c.status)}>{c.status.replace("_", " ")}</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="actions">
            <Card>
              <CardContent className="pt-6">
                {actions.length === 0 ? (
                  <p className="text-sm text-gray-400">No action items yet.</p>
                ) : (
                  <div className="space-y-3">
                    {actions.map((a) => (
                      <div key={a.id} className="flex items-center justify-between border-b last:border-0 pb-3 last:pb-0">
                        <div>
                          <div className="font-medium">{a.title}</div>
                          <div className="text-xs text-gray-500 mt-0.5">{a.status} — {a.priority}</div>
                        </div>
                        <Badge className={a.status === "completed" ? "bg-green-500 text-white" : "bg-yellow-500 text-black"}>
                          {a.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
