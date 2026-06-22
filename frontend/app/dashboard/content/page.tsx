"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuthStore } from "@/lib/auth";
import api from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Wand2, Trash2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Content {
  id: string;
  type: string;
  title: string;
  status: string;
  credits_used: number;
  metadata_: { word_count?: number };
  created_at: string;
}

const STATUS_COLORS: Record<string, "default" | "secondary" | "success" | "warning"> = {
  draft: "secondary",
  published: "success",
  scheduled: "warning",
  archived: "default",
};

export default function ContentPage() {
  const { activeWorkspace } = useAuthStore();
  const [items, setItems] = useState<Content[]>([]);
  const [filter, setFilter] = useState("");

  const fetchContent = () => {
    if (!activeWorkspace) return;
    const q = filter ? `&content_type=${filter}` : "";
    api.get(`/workspaces/${activeWorkspace.id}/content?limit=50${q}`)
      .then((r) => setItems(r.data))
      .catch(() => {});
  };

  useEffect(() => { fetchContent(); }, [activeWorkspace, filter]);

  const handleDelete = async (id: string) => {
    if (!activeWorkspace || !confirm("Delete this content?")) return;
    await api.delete(`/workspaces/${activeWorkspace.id}/content/${id}`);
    fetchContent();
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Content Library</h1>
        <Button asChild><Link href="/dashboard/generate"><Wand2 className="h-4 w-4" /> Generate new</Link></Button>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        {["", "newsletter", "blog", "linkedin", "twitter_thread", "summary"].map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setFilter(t)}
            className={`px-3 py-1 rounded-full border text-xs font-medium capitalize transition-all ${
              filter === t ? "border-zinc-900 bg-zinc-900 text-white" : "border-zinc-200 text-zinc-600 hover:border-zinc-400"
            }`}
          >
            {t || "All"}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {items.length === 0 && (
          <div className="text-center py-12 text-zinc-400">
            No content yet. <Link href="/dashboard/generate" className="text-zinc-600 hover:underline">Generate your first piece →</Link>
          </div>
        )}
        {items.map((item) => (
          <Card key={item.id} className="hover:shadow-md transition-shadow">
            <CardContent className="py-3 px-4 flex items-center gap-4">
              <div className="flex-1 min-w-0">
                <Link href={`/dashboard/content/${item.id}`} className="hover:underline">
                  <p className="font-medium text-sm">{item.title || "Untitled"}</p>
                </Link>
                <p className="text-xs text-zinc-400 mt-0.5">
                  {item.type.replace("_", " ")}
                  {item.metadata_?.word_count ? ` · ${item.metadata_.word_count} words` : ""}
                  {` · ${item.credits_used} credits`}
                  {` · ${formatDistanceToNow(new Date(item.created_at))} ago`}
                </p>
              </div>
              <Badge variant={STATUS_COLORS[item.status] || "default"}>{item.status}</Badge>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleDelete(item.id)}
                className="text-zinc-300 hover:text-red-500"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
