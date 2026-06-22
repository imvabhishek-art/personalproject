"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock, Send, Trash2, Plus } from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";

interface Schedule {
  id: string;
  generated_content_id: string;
  send_at: string;
  cron_expression: string | null;
  recipient_list: { emails?: string[]; sendgrid_list_id?: string };
  is_active: boolean;
  last_sent_at: string | null;
  status: string;
  content?: { title: string; type: string };
}

interface ContentItem {
  id: string;
  title: string;
  type: string;
  status: string;
}

export default function SchedulesPage() {
  const { activeWorkspace } = useAuthStore();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [sending, setSending] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState({
    generated_content_id: "",
    send_at: "",
    cron_expression: "",
    emails: "",
    sendgrid_list_id: "",
  });

  const fetchSchedules = () => {
    if (!activeWorkspace) return;
    api.get(`/workspaces/${activeWorkspace.id}/schedules`)
      .then((r) => setSchedules(r.data))
      .catch(() => {});
  };

  useEffect(() => {
    if (!activeWorkspace) return;
    fetchSchedules();
    api.get(`/workspaces/${activeWorkspace.id}/content?limit=100`)
      .then((r) => setContent(r.data))
      .catch(() => {});
  }, [activeWorkspace]);

  const handleCreate = async () => {
    if (!activeWorkspace || !form.generated_content_id || !form.send_at) return;
    setSaving(true);
    const emails = form.emails.split(",").map((e) => e.trim()).filter(Boolean);
    const recipient_list = form.sendgrid_list_id
      ? { sendgrid_list_id: form.sendgrid_list_id }
      : { emails };

    try {
      await api.post(`/workspaces/${activeWorkspace.id}/schedules`, {
        generated_content_id: form.generated_content_id,
        send_at: new Date(form.send_at).toISOString(),
        cron_expression: form.cron_expression || null,
        recipient_list,
      });
      setShowAdd(false);
      setForm({ generated_content_id: "", send_at: "", cron_expression: "", emails: "", sendgrid_list_id: "" });
      fetchSchedules();
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to create schedule");
    } finally {
      setSaving(false);
    }
  };

  const handleSendNow = async (id: string) => {
    if (!activeWorkspace) return;
    setSending(id);
    try {
      await api.post(`/workspaces/${activeWorkspace.id}/schedules/${id}/send-now`);
      setTimeout(() => { fetchSchedules(); setSending(null); }, 1500);
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to send");
      setSending(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!activeWorkspace || !confirm("Delete this schedule?")) return;
    await api.delete(`/workspaces/${activeWorkspace.id}/schedules/${id}`);
    fetchSchedules();
  };

  const STATUS_COLORS: Record<string, "default" | "secondary" | "success" | "warning"> = {
    pending: "warning",
    sent: "success",
    failed: "default",
    cancelled: "secondary",
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Schedules</h1>
        <Button onClick={() => setShowAdd((v) => !v)}><Plus className="h-4 w-4" /> New schedule</Button>
      </div>

      {showAdd && (
        <Card className="mb-6">
          <CardContent className="pt-4 space-y-4">
            <div>
              <Label>Content to send</Label>
              <select
                value={form.generated_content_id}
                onChange={(e) => setForm((f) => ({ ...f, generated_content_id: e.target.value }))}
                className="mt-1 w-full border border-zinc-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-900 bg-white"
              >
                <option value="">Select content...</option>
                {content.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title || "Untitled"} ({c.type.replace("_", " ")})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label>Send at</Label>
              <Input
                type="datetime-local"
                value={form.send_at}
                onChange={(e) => setForm((f) => ({ ...f, send_at: e.target.value }))}
                className="mt-1"
              />
            </div>

            <div>
              <Label>Recurring? (cron expression, optional)</Label>
              <Input
                value={form.cron_expression}
                onChange={(e) => setForm((f) => ({ ...f, cron_expression: e.target.value }))}
                placeholder="0 9 * * 1  (every Monday at 9am)"
                className="mt-1"
              />
            </div>

            <div>
              <Label>Recipient emails (comma-separated)</Label>
              <Input
                value={form.emails}
                onChange={(e) => setForm((f) => ({ ...f, emails: e.target.value }))}
                placeholder="alice@example.com, bob@example.com"
                className="mt-1"
              />
            </div>

            <div>
              <Label>— or — SendGrid list ID</Label>
              <Input
                value={form.sendgrid_list_id}
                onChange={(e) => setForm((f) => ({ ...f, sendgrid_list_id: e.target.value }))}
                placeholder="sendgrid-list-uuid"
                className="mt-1"
              />
            </div>

            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowAdd(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={saving || !form.generated_content_id || !form.send_at}>
                {saving ? "Saving..." : "Create schedule"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {schedules.length === 0 && (
          <div className="text-center py-12 text-zinc-400">
            No schedules yet. Create one to send content automatically.
          </div>
        )}
        {schedules.map((sched) => (
          <Card key={sched.id}>
            <CardContent className="py-4 px-4 flex items-center gap-4">
              <div className="p-2 rounded-lg bg-zinc-100 text-zinc-600">
                {sched.cron_expression ? <Clock className="h-4 w-4" /> : <Calendar className="h-4 w-4" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">
                  {sched.content?.title || "Content #" + sched.generated_content_id.slice(0, 8)}
                </p>
                <p className="text-xs text-zinc-400 mt-0.5">
                  {sched.cron_expression
                    ? `Recurring: ${sched.cron_expression}`
                    : `Sends ${formatDistanceToNow(new Date(sched.send_at))} from now`}
                  {sched.last_sent_at && ` · Last sent ${format(new Date(sched.last_sent_at), "MMM d, HH:mm")}`}
                </p>
              </div>
              <Badge variant={STATUS_COLORS[sched.status] || "default"}>{sched.status}</Badge>
              <div className="flex gap-1.5">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleSendNow(sched.id)}
                  disabled={sending === sched.id}
                  title="Send now"
                >
                  <Send className={`h-4 w-4 ${sending === sched.id ? "opacity-50" : ""}`} />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleDelete(sched.id)}
                  className="text-zinc-400 hover:text-red-500"
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
