"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listActionItems, updateActionItem, deleteActionItem, type ActionItem, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";

function priorityColor(p: string) {
  switch (p) {
    case "critical": return "bg-red-600 text-white";
    case "high": return "bg-orange-500 text-white";
    case "medium": return "bg-yellow-500 text-black";
    default: return "bg-blue-500 text-white";
  }
}

const columns: ActionItem["status"][] = ["pending", "in_progress", "blocked", "completed"];

export default function ActionItemsPage() {
  const [items, setItems] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>("");

  async function load() {
    setLoading(true);
    try {
      const params: { status?: string } = {};
      if (filterStatus) params.status = filterStatus;
      const data = await listActionItems(params);
      setItems(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [filterStatus]);

  async function moveStatus(id: string, newStatus: ActionItem["status"]) {
    try {
      await updateActionItem(id, { status: newStatus });
      load();
    } catch (err) {
      alert("Failed to update status");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this action item?")) return;
    try {
      await deleteActionItem(id);
      load();
    } catch (err) {
      alert("Delete failed");
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Action Items</h1>
          <p className="text-sm text-gray-500">Track and manage response tasks</p>
        </div>
        <div className="flex gap-3">
          <Link href="/dashboard"><Button variant="outline">Dashboard</Button></Link>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto space-y-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <Select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            
            
              <option value=" ">All statuses</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="blocked">Blocked</option>
              <option value="completed">Completed</option>
            
          </Select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {columns.map((col) => (
            <Card key={col}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold capitalize">{col.replace("_", " ")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {items.filter((i) => i.status === col).length === 0 ? (
                  <p className="text-xs text-gray-400">No items</p>
                ) : (
                  items
                    .filter((i) => i.status === col)
                    .map((item) => (
                      <div key={item.id} className="border rounded p-3 bg-white space-y-2">
                        <div className="font-medium text-sm">{item.title}</div>
                        <div className="flex gap-1 flex-wrap">
                          <Badge className={priorityColor(item.priority)}>{item.priority}</Badge>
                        </div>
                        <div className="flex gap-1 flex-wrap">
                          {columns.filter((c) => c !== item.status).map((c) => (
                            <Button key={c} size="sm" variant="outline" className="text-xs px-2 py-0.5 h-auto" onClick={() => moveStatus(item.id, c)}>
                              Move to {c.replace("_", " ")}
                            </Button>
                          ))}
                        </div>
                        <Button size="sm" variant="destructive" className="text-xs w-full" onClick={() => handleDelete(item.id)}>Delete</Button>
                      </div>
                    ))
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}
