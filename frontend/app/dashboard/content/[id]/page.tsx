"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft, Save, Copy } from "lucide-react";

interface Content {
  id: string;
  type: string;
  title: string;
  subject_line: string | null;
  body_md: string;
  body_html: string;
  status: string;
  credits_used: number;
  metadata_: { word_count?: number; model_used?: string };
  created_at: string;
}

export default function ContentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { activeWorkspace } = useAuthStore();
  const [content, setContent] = useState<Content | null>(null);
  const [title, setTitle] = useState("");
  const [subjectLine, setSubjectLine] = useState("");
  const [bodyMd, setBodyMd] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!activeWorkspace || !id) return;
    api.get(`/workspaces/${activeWorkspace.id}/content/${id}`)
      .then((r) => {
        setContent(r.data);
        setTitle(r.data.title);
        setSubjectLine(r.data.subject_line || "");
        setBodyMd(r.data.body_md);
      })
      .catch(() => router.push("/dashboard/content"));
  }, [activeWorkspace, id]);

  const handleSave = async () => {
    if (!activeWorkspace || !content) return;
    setSaving(true);
    try {
      await api.patch(`/workspaces/${activeWorkspace.id}/content/${content.id}`, {
        title,
        subject_line: subjectLine || null,
        body_md: bodyMd,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(bodyMd);
  };

  if (!content) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-6 w-6 border-2 border-zinc-900 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="text-xl font-bold border-0 bg-transparent px-0 focus-visible:ring-0 h-auto py-0"
            placeholder="Untitled"
          />
        </div>
        <Badge variant="secondary">{content.type.replace("_", " ")}</Badge>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={handleCopy} title="Copy Markdown">
            <Copy className="h-4 w-4" />
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            <Save className="h-4 w-4" />
            {saving ? "Saving..." : saved ? "Saved!" : "Save"}
          </Button>
        </div>
      </div>

      {content.type === "newsletter" && (
        <div className="mb-4">
          <Input
            value={subjectLine}
            onChange={(e) => setSubjectLine(e.target.value)}
            placeholder="Email subject line..."
            className="text-sm"
          />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Markdown editor */}
        <div>
          <p className="text-xs text-zinc-500 mb-2 font-medium">MARKDOWN</p>
          <textarea
            value={bodyMd}
            onChange={(e) => setBodyMd(e.target.value)}
            className="w-full h-[60vh] font-mono text-sm p-3 border border-zinc-200 rounded-lg resize-none focus:outline-none focus:ring-1 focus:ring-zinc-900 bg-white"
            placeholder="Start writing..."
          />
        </div>

        {/* HTML preview */}
        <div>
          <p className="text-xs text-zinc-500 mb-2 font-medium">PREVIEW</p>
          <div
            className="w-full h-[60vh] overflow-y-auto p-4 border border-zinc-200 rounded-lg bg-white prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: content.body_html }}
          />
        </div>
      </div>

      <div className="mt-4 flex items-center gap-4 text-xs text-zinc-400">
        {content.metadata_?.word_count && <span>{content.metadata_.word_count} words</span>}
        {content.metadata_?.model_used && <span>{content.metadata_.model_used}</span>}
        <span>{content.credits_used} credits used</span>
      </div>
    </div>
  );
}
