"use client";

import Link from "next/link";
import { AlertTriangle, Activity, Flame } from "lucide-react";
import type { ActionItem, Crisis } from "@/lib/api";
import { cn } from "@/lib/utils";

interface SituationMapProps {
  crises: Crisis[];
  actions: ActionItem[];
}

const SEVERITY_ROWS: { key: Crisis["severity"]; label: string; color: string }[] = [
  { key: "critical", label: "Critical", color: "bg-red-600" },
  { key: "high", label: "High", color: "bg-orange-500" },
  { key: "medium", label: "Medium", color: "bg-yellow-500" },
  { key: "low", label: "Low", color: "bg-blue-500" },
];

const ACTIVE_STATUSES: ReadonlySet<Crisis["status"]> = new Set<Crisis["status"]>(["detected", "assessing", "responding"]);

function statusBadgeClass(status: Crisis["status"]) {
  switch (status) {
    case "responding":
      return "bg-indigo-600";
    case "assessing":
      return "bg-purple-600";
    case "detected":
      return "bg-slate-600";
    case "contained":
      return "bg-teal-600";
    default:
      return "bg-gray-500";
  }
}

function ageString(detected: string) {
  const ms = Date.now() - new Date(detected).getTime();
  const min = Math.max(0, Math.floor(ms / 60000));
  if (min < 60) return `${min}m`;
  const hr = Math.floor(min / 60);
  if (hr < 48) return `${hr}h`;
  return `${Math.floor(hr / 24)}d`;
}

function isStale(c: Crisis): boolean {
  if (c.severity !== "critical") return false;
  if (!ACTIVE_STATUSES.has(c.status)) return false;
  const detectedMs = new Date(c.detected_at || c.created_at).getTime();
  return Date.now() - detectedMs > 60 * 60 * 1000; // > 1h
}

export function SituationMap({ crises, actions }: SituationMapProps) {
  const active = crises.filter((c) => ACTIVE_STATUSES.has(c.status));

  if (active.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6 text-center text-sm text-gray-500">
        No active crises. All clear.
      </div>
    );
  }

  // Group active crises by severity for the timeline rows.
  const byRow = new Map<Crisis["severity"], Crisis[]>();
  for (const row of SEVERITY_ROWS) byRow.set(row.key, []);
  for (const c of active) byRow.get(c.severity)?.push(c);
  byRow.forEach((list) => list.sort((a: Crisis, b: Crisis) => new Date(b.detected_at || b.created_at).getTime() - new Date(a.detected_at || a.created_at).getTime()));

  const counts = { critical: byRow.get("critical")?.length ?? 0, high: byRow.get("high")?.length ?? 0, total: active.length };
  const staleCriticalCount = active.filter(isStale).length;

  // Aggregate action progress per crisis.
  const actionsByCrisis = new Map<string, { total: number; done: number; blocked: number }>();
  for (const a of actions) {
    const bucket = actionsByCrisis.get(a.crisis_id) ?? { total: 0, done: 0, blocked: 0 };
    bucket.total += 1;
    if (a.status === "completed") bucket.done += 1;
    if (a.status === "blocked") bucket.blocked += 1;
    actionsByCrisis.set(a.crisis_id, bucket);
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200">
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-pink-600" />
          <h2 className="font-semibold">Situation Map</h2>
          <span className="text-xs text-gray-500">{counts.total} active</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {counts.critical > 0 && (
            <span className="bg-red-50 border border-red-200 text-red-700 rounded px-2 py-0.5 flex items-center gap-1">
              <Flame className="h-3 w-3" /> {counts.critical} critical
            </span>
          )}
          {counts.high > 0 && (
            <span className="bg-orange-50 border border-orange-200 text-orange-700 rounded px-2 py-0.5">
              {counts.high} high
            </span>
          )}
          {staleCriticalCount > 0 && (
            <span className="bg-red-100 border border-red-300 text-red-800 rounded px-2 py-0.5 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" /> {staleCriticalCount} stale critical (&gt;1h)
            </span>
          )}
        </div>
      </div>
      <div className="p-3 space-y-1.5">
        {SEVERITY_ROWS.map((row) => {
          const items = byRow.get(row.key) ?? [];
          return (
            <div key={row.key} className="flex items-center gap-3">
              <div className={cn("w-24 text-xs font-medium uppercase tracking-wide flex items-center gap-1.5", items.length === 0 && "opacity-40")}>
                <span className={cn("w-2 h-2 rounded-full", row.color)} />
                {row.label}
              </div>
              <div className="flex-1 min-w-0 flex flex-wrap gap-2 py-1">
                {items.length === 0 ? (
                  <div className="text-xs text-gray-300 italic">—</div>
                ) : (
                  items.map((c) => {
                    const a = actionsByCrisis.get(c.id);
                    const progress = a && a.total > 0 ? Math.round((a.done / a.total) * 100) : null;
                    const stale = isStale(c);
                    return (
                      <Link
                        key={c.id}
                        href={`/crisis/${c.id}`}
                        className={cn(
                          "group rounded-md border bg-slate-50 hover:bg-slate-100 hover:border-slate-300 transition px-3 py-2 min-w-[180px] max-w-[260px] flex flex-col gap-1",
                          stale && "border-red-400 bg-red-50 hover:bg-red-100",
                        )}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="text-sm font-medium truncate">{c.title}</div>
                          {stale && <AlertTriangle className="h-3.5 w-3.5 text-red-600 shrink-0" />}
                        </div>
                        <div className="flex items-center gap-2 text-[11px] text-slate-600">
                          <span className={cn("inline-block text-white text-[10px] px-1.5 py-0.5 rounded", statusBadgeClass(c.status))}>
                            {c.status.replace("_", " ")}
                          </span>
                          <span className="text-gray-500">{c.category.replace("_", " ")}</span>
                          <span className="ml-auto text-gray-500">{ageString(c.detected_at || c.created_at)}</span>
                        </div>
                        {progress !== null && (
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-1.5 bg-slate-200 rounded overflow-hidden">
                              <div className="h-full bg-emerald-500" style={{ width: `${progress}%` }} />
                            </div>
                            <span className="text-[10px] text-gray-500 tabular-nums">{a?.done}/{a?.total}</span>
                            {a && a.blocked > 0 && (
                              <span className="text-[10px] text-red-600">{a.blocked} blocked</span>
                            )}
                          </div>
                        )}
                      </Link>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
