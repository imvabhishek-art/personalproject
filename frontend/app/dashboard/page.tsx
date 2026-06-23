"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/auth";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Wand2, Rss, FileText, CreditCard } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface ContentItem {
  id: string;
  type: string;
  title: string;
  status: string;
  credits_used: number;
  created_at: string;
}

const STATUS_COLORS: Record<string, "default" | "secondary" | "success" | "warning"> = {
  draft: "secondary",
  published: "success",
  scheduled: "warning",
  archived: "default",
};

export default function DashboardPage() {
  const { activeWorkspace } = useAuthStore();
  const router = useRouter();
  const [content, setContent] = useState<ContentItem[]>([]);
  const [balance, setBalance] = useState<number | null>(null);
  const [sourcesCount, setSourcesCount] = useState(0);

  useEffect(() => {
    if (!activeWorkspace) return;

    const wsId = activeWorkspace.id;
    Promise.all([
      api.get(`/workspaces/${wsId}/content?limit=5`),
      api.get(`/workspaces/${wsId}/credits/balance`),
      api.get(`/workspaces/${wsId}/sources`),
    ]).then(([c, b, s]) => {
      setContent(c.data);
      setBalance(b.data.balance);
      setSourcesCount(s.data.length);
    }).catch(() => {});
  }, [activeWorkspace]);

  if (!activeWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-zinc-500 mb-4">No workspace found.</p>
          <Button onClick={() => router.push("/onboarding")}>Create workspace</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-900">Dashboard</h1>
        <p className="text-zinc-500 text-sm mt-1">{activeWorkspace.name}</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-zinc-100">
                <CreditCard className="h-4 w-4 text-zinc-600" />
              </div>
              <div>
                <p className="text-xs text-zinc-500">Credits</p>
                <p className="text-xl font-bold">{balance ?? "—"}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-zinc-100">
                <Rss className="h-4 w-4 text-zinc-600" />
              </div>
              <div>
                <p className="text-xs text-zinc-500">Sources</p>
                <p className="text-xl font-bold">{sourcesCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-zinc-100">
                <FileText className="h-4 w-4 text-zinc-600" />
              </div>
              <div>
                <p className="text-xs text-zinc-500">Content pieces</p>
                <p className="text-xl font-bold">{content.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick actions */}
      <div className="flex gap-3 mb-6">
        <Button asChild>
          <Link href="/dashboard/generate"><Wand2 className="h-4 w-4" /> Generate content</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/dashboard/sources"><Rss className="h-4 w-4" /> Add source</Link>
        </Button>
        {balance !== null && balance < 20 && (
          <Button variant="outline" asChild>
            <Link href="/dashboard/credits"><CreditCard className="h-4 w-4" /> Buy credits</Link>
          </Button>
        )}
      </div>

      {/* Recent content */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Recent content</CardTitle>
            <Link href="/dashboard/content" className="text-sm text-zinc-500 hover:text-zinc-800">
              View all →
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {content.length === 0 ? (
            <div className="text-center py-8 text-zinc-400 text-sm">
              No content yet.{" "}
              <Link href="/dashboard/generate" className="text-zinc-600 hover:underline">Generate your first piece →</Link>
            </div>
          ) : (
            <div className="divide-y divide-zinc-100">
              {content.map((item) => (
                <Link
                  key={item.id}
                  href={`/dashboard/content/${item.id}`}
                  className="flex items-center justify-between py-3 hover:bg-zinc-50 -mx-2 px-2 rounded transition-colors"
                >
                  <div>
                    <p className="text-sm font-medium text-zinc-900">{item.title || "Untitled"}</p>
                    <p className="text-xs text-zinc-400 mt-0.5">
                      {item.type.replace("_", " ")} · {formatDistanceToNow(new Date(item.created_at))} ago
                    </p>
                  </div>
                  <Badge variant={STATUS_COLORS[item.status] || "default"}>
                    {item.status}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
