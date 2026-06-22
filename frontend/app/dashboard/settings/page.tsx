"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { UserPlus, Trash2 } from "lucide-react";

type Tab = "general" | "profile" | "members";

interface Member {
  user_id: string;
  role: string;
  email: string;
  full_name: string;
  joined_at: string;
}

export default function SettingsPage() {
  const { activeWorkspace, fetchWorkspaces } = useAuthStore();
  const [tab, setTab] = useState<Tab>("general");
  const [name, setName] = useState("");
  const [savingName, setSavingName] = useState(false);
  const [members, setMembers] = useState<Member[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("editor");
  const [inviting, setInviting] = useState(false);

  // Profile state
  const [profile, setProfile] = useState({
    audience: "",
    persona: "creator",
    tone: "conversational",
    topics: "",
    brand_name: "",
    writing_style: "",
  });
  const [savingProfile, setSavingProfile] = useState(false);

  useEffect(() => {
    if (!activeWorkspace) return;
    setName(activeWorkspace.name);
    if (activeWorkspace.profile) {
      const p = activeWorkspace.profile as Record<string, string>;
      setProfile({
        audience: p.audience || "",
        persona: p.persona || "creator",
        tone: p.tone || "conversational",
        topics: Array.isArray(p.topics) ? (p.topics as unknown as string[]).join(", ") : (p.topics || ""),
        brand_name: p.brand_name || "",
        writing_style: p.writing_style || "",
      });
    }
    api.get(`/workspaces/${activeWorkspace.id}/members`)
      .then((r) => setMembers(r.data))
      .catch(() => {});
  }, [activeWorkspace]);

  const handleSaveName = async () => {
    if (!activeWorkspace) return;
    setSavingName(true);
    try {
      await api.patch(`/workspaces/${activeWorkspace.id}`, { name });
      await fetchWorkspaces();
    } finally {
      setSavingName(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!activeWorkspace) return;
    setSavingProfile(true);
    try {
      const topics = profile.topics.split(",").map((t) => t.trim()).filter(Boolean);
      await api.post(`/workspaces/${activeWorkspace.id}/onboarding`, {
        ...profile,
        topics,
        content_types: activeWorkspace.profile?.content_types || [],
      });
      await fetchWorkspaces();
    } finally {
      setSavingProfile(false);
    }
  };

  const handleInvite = async () => {
    if (!activeWorkspace || !inviteEmail) return;
    setInviting(true);
    try {
      await api.post(`/workspaces/${activeWorkspace.id}/members/invite`, {
        email: inviteEmail,
        role: inviteRole,
      });
      setInviteEmail("");
      const r = await api.get(`/workspaces/${activeWorkspace.id}/members`);
      setMembers(r.data);
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to invite");
    } finally {
      setInviting(false);
    }
  };

  const handleRemove = async (userId: string) => {
    if (!activeWorkspace || !confirm("Remove this member?")) return;
    await api.delete(`/workspaces/${activeWorkspace.id}/members/${userId}`);
    setMembers((m) => m.filter((x) => x.user_id !== userId));
  };

  const TABS: { id: Tab; label: string }[] = [
    { id: "general", label: "General" },
    { id: "profile", label: "Workspace profile" },
    { id: "members", label: "Members" },
  ];

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="flex gap-1 mb-6 border-b border-zinc-200">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
              tab === t.id
                ? "border-zinc-900 text-zinc-900"
                : "border-transparent text-zinc-500 hover:text-zinc-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "general" && (
        <Card>
          <CardHeader>
            <CardTitle>Workspace name</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} className="mt-1 max-w-sm" />
            </div>
            <Button onClick={handleSaveName} disabled={savingName}>
              {savingName ? "Saving..." : "Save changes"}
            </Button>
          </CardContent>
        </Card>
      )}

      {tab === "profile" && (
        <Card>
          <CardHeader>
            <CardTitle>Content profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Target audience</Label>
              <Input
                value={profile.audience}
                onChange={(e) => setProfile((p) => ({ ...p, audience: e.target.value }))}
                placeholder="e.g. early-stage startup founders in SaaS"
                className="mt-1"
              />
            </div>

            <div>
              <Label>Persona</Label>
              <div className="flex gap-2 mt-1 flex-wrap">
                {["creator", "brand", "agency"].map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setProfile((p) => ({ ...p, persona: v }))}
                    className={`px-3 py-1.5 rounded-md border text-sm capitalize transition-all ${
                      profile.persona === v
                        ? "border-zinc-900 bg-zinc-900 text-white"
                        : "border-zinc-200 bg-white hover:border-zinc-400"
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <Label>Tone</Label>
              <div className="flex gap-2 mt-1 flex-wrap">
                {["formal", "conversational", "witty", "authoritative"].map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setProfile((p) => ({ ...p, tone: v }))}
                    className={`px-3 py-1.5 rounded-md border text-sm capitalize transition-all ${
                      profile.tone === v
                        ? "border-zinc-900 bg-zinc-900 text-white"
                        : "border-zinc-200 bg-white hover:border-zinc-400"
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <Label>Topics (comma-separated)</Label>
              <Input
                value={profile.topics}
                onChange={(e) => setProfile((p) => ({ ...p, topics: e.target.value }))}
                placeholder="AI tools, productivity, SaaS growth"
                className="mt-1"
              />
            </div>

            <div>
              <Label>Brand name</Label>
              <Input
                value={profile.brand_name}
                onChange={(e) => setProfile((p) => ({ ...p, brand_name: e.target.value }))}
                placeholder="Acme Corp"
                className="mt-1 max-w-sm"
              />
            </div>

            <div>
              <Label>Writing style guidelines</Label>
              <Textarea
                value={profile.writing_style}
                onChange={(e) => setProfile((p) => ({ ...p, writing_style: e.target.value }))}
                placeholder="Short punchy sentences. No jargon. Always end with a clear call to action."
                rows={3}
                className="mt-1"
              />
            </div>

            <Button onClick={handleSaveProfile} disabled={savingProfile}>
              {savingProfile ? "Saving..." : "Save profile"}
            </Button>
          </CardContent>
        </Card>
      )}

      {tab === "members" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Invite member</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="email@example.com"
                  className="flex-1"
                />
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="border border-zinc-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-900 bg-white"
                >
                  <option value="editor">Editor</option>
                  <option value="viewer">Viewer</option>
                </select>
                <Button onClick={handleInvite} disabled={inviting || !inviteEmail}>
                  <UserPlus className="h-4 w-4" />
                  {inviting ? "Inviting..." : "Invite"}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Members</CardTitle>
            </CardHeader>
            <CardContent className="divide-y divide-zinc-100 p-0">
              {members.map((m) => (
                <div key={m.user_id} className="flex items-center justify-between px-6 py-3">
                  <div>
                    <p className="text-sm font-medium">{m.full_name || m.email}</p>
                    <p className="text-xs text-zinc-400">{m.email}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary" className="capitalize">{m.role}</Badge>
                    {m.role !== "owner" && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRemove(m.user_id)}
                        className="text-zinc-300 hover:text-red-500"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
