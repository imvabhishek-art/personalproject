"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Rss, Globe, Twitter, Linkedin, FileText, Plus, RefreshCw, Trash2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Source {
  id: string;
  type: string;
  name: string;
  config: Record<string, string>;
  is_active: boolean;
  last_synced_at: string | null;
  created_at: string;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  rss: <Rss className="h-4 w-4" />,
  scrape: <Globe className="h-4 w-4" />,
  twitter: <Twitter className="h-4 w-4" />,
  linkedin: <Linkedin className="h-4 w-4" />,
  manual: <FileText className="h-4 w-4" />,
};

export default function SourcesPage() {
  const { activeWorkspace } = useAuthStore();
  const [sources, setSources] = useState<Source[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [addType, setAddType] = useState("rss");
  const [addName, setAddName] = useState("");
  const [addConfig, setAddConfig] = useState<Record<string, string>>({});
  const [adding, setAdding] = useState(false);
  const [syncing, setSyncing] = useState<string | null>(null);

  const fetchSources = () => {
    if (!activeWorkspace) return;
    api.get(`/workspaces/${activeWorkspace.id}/sources`)
      .then((r) => setSources(r.data))
      .catch(() => {});
  };

  useEffect(() => { fetchSources(); }, [activeWorkspace]);

  const handleAdd = async () => {
    if (!activeWorkspace || !addName) return;
    setAdding(true);
    try {
      await api.post(`/workspaces/${activeWorkspace.id}/sources`, {
        type: addType, name: addName, config: addConfig,
      });
      setShowAdd(false);
      setAddName("");
      setAddConfig({});
      fetchSources();
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to add source");
    } finally {
      setAdding(false);
    }
  };

  const handleSync = async (id: string) => {
    if (!activeWorkspace) return;
    setSyncing(id);
    try {
      await api.post(`/workspaces/${activeWorkspace.id}/sources/${id}/fetch`);
      setTimeout(() => { fetchSources(); setSyncing(null); }, 2000);
    } catch { setSyncing(null); }
  };

  const handleDelete = async (id: string) => {
    if (!activeWorkspace || !confirm("Delete this source?")) return;
    await api.delete(`/workspaces/${activeWorkspace.id}/sources/${id}`);
    fetchSources();
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Content Sources</h1>
        <Button onClick={() => setShowAdd((v) => !v)}><Plus className="h-4 w-4" /> Add source</Button>
      </div>

      {showAdd && (
        <Card className="mb-6">
          <CardContent className="pt-4 space-y-4">
            <div>
              <Label>Source type</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {["rss", "scrape", "twitter", "linkedin", "manual"].map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => { setAddType(t); setAddConfig({}); }}
                    className={`px-3 py-1.5 rounded-md border text-sm font-medium capitalize transition-all ${
                      addType === t ? "border-zinc-900 bg-zinc-900 text-white" : "border-zinc-200 bg-white hover:border-zinc-400"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Label>Name</Label>
              <Input value={addName} onChange={(e) => setAddName(e.target.value)} placeholder="My RSS Feed" className="mt-1" />
            </div>
            {addType === "rss" && (
              <div>
                <Label>Feed URL</Label>
                <Input value={addConfig.feed_url || ""} onChange={(e) => setAddConfig({ feed_url: e.target.value })} placeholder="https://example.com/feed.xml" className="mt-1" />
              </div>
            )}
            {addType === "scrape" && (
              <>
                <div>
                  <Label>Page URL</Label>
                  <Input value={addConfig.page_url || ""} onChange={(e) => setAddConfig((c) => ({ ...c, page_url: e.target.value }))} placeholder="https://example.com/blog" className="mt-1" />
                </div>
                <div>
                  <Label>CSS selector (optional)</Label>
                  <Input value={addConfig.css_selector || ""} onChange={(e) => setAddConfig((c) => ({ ...c, css_selector: e.target.value }))} placeholder="article, .post-content" className="mt-1" />
                </div>
              </>
            )}
            {addType === "twitter" && (
              <div>
                <Label>Twitter handle or keywords</Label>
                <Input value={addConfig.handle || ""} onChange={(e) => setAddConfig({ handle: e.target.value })} placeholder="@handle or #keyword" className="mt-1" />
              </div>
            )}
            {addType === "linkedin" && (
              <div>
                <Label>Organization URN (from LinkedIn API)</Label>
                <Input value={addConfig.organization_urn || ""} onChange={(e) => setAddConfig({ organization_urn: e.target.value, access_token: addConfig.access_token || "" })} placeholder="urn:li:organization:12345" className="mt-1" />
              </div>
            )}
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowAdd(false)}>Cancel</Button>
              <Button onClick={handleAdd} disabled={adding}>{adding ? "Adding..." : "Add source"}</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {sources.length === 0 && (
          <div className="text-center py-12 text-zinc-400">
            No sources yet. Add an RSS feed, website, or social account to start curating content.
          </div>
        )}
        {sources.map((source) => (
          <Card key={source.id}>
            <CardContent className="py-4 px-4 flex items-center gap-4">
              <div className="p-2 rounded-lg bg-zinc-100 text-zinc-600">
                {TYPE_ICONS[source.type] || <Rss className="h-4 w-4" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm">{source.name}</p>
                <p className="text-xs text-zinc-400 mt-0.5 truncate">
                  {Object.values(source.config)[0] || source.type}
                  {source.last_synced_at && ` · Synced ${formatDistanceToNow(new Date(source.last_synced_at))} ago`}
                </p>
              </div>
              <Badge variant={source.is_active ? "success" : "secondary"}>
                {source.is_active ? "active" : "inactive"}
              </Badge>
              <div className="flex gap-1.5">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleSync(source.id)}
                  disabled={syncing === source.id}
                  title="Sync now"
                >
                  <RefreshCw className={`h-4 w-4 ${syncing === source.id ? "animate-spin" : ""}`} />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleDelete(source.id)}
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
