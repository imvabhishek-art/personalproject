"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const CONTENT_TYPES = [
  { value: "newsletter", label: "Newsletter", credits: 10 },
  { value: "blog", label: "Blog Post", credits: 8 },
  { value: "linkedin", label: "LinkedIn Post", credits: 3 },
  { value: "twitter_thread", label: "Twitter Thread", credits: 4 },
  { value: "summary", label: "Summary", credits: 2 },
];

export default function GeneratePage() {
  const router = useRouter();
  const { activeWorkspace } = useAuthStore();
  const [contentType, setContentType] = useState("newsletter");
  const [instructions, setInstructions] = useState("");
  const [topic, setTopic] = useState("");
  const [balance, setBalance] = useState<number | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>("");
  const [progress, setProgress] = useState<string>("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const selectedType = CONTENT_TYPES.find((t) => t.value === contentType);

  useEffect(() => {
    if (!activeWorkspace) return;
    api.get(`/workspaces/${activeWorkspace.id}/credits/balance`)
      .then((r) => setBalance(r.data.balance))
      .catch(() => {});
  }, [activeWorkspace]);

  useEffect(() => {
    if (!jobId || !activeWorkspace) return;

    pollRef.current = setInterval(async () => {
      try {
        const { data } = await api.get(`/workspaces/${activeWorkspace.id}/generate/${jobId}`);
        setJobStatus(data.status);
        setProgress(data.progress || "");

        if (data.status === "complete" && data.content_id) {
          clearInterval(pollRef.current!);
          router.push(`/dashboard/content/${data.content_id}`);
        } else if (data.status === "failed") {
          clearInterval(pollRef.current!);
          setError(data.error || "Generation failed");
          setLoading(false);
          setJobId(null);
        }
      } catch {
        clearInterval(pollRef.current!);
        setLoading(false);
      }
    }, 2000);

    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [jobId, activeWorkspace, router]);

  const handleGenerate = async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    setError("");
    setJobStatus("");
    setProgress("");

    try {
      const { data } = await api.post(`/workspaces/${activeWorkspace.id}/generate`, {
        type: contentType,
        instructions,
        topic,
      });
      setJobId(data.job_id);
      setJobStatus("queued");
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to start generation");
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Generate Content</h1>

      <div className="space-y-5">
        <div>
          <Label className="mb-2 block">Content type</Label>
          <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
            {CONTENT_TYPES.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => setContentType(t.value)}
                className={`px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
                  contentType === t.value
                    ? "border-zinc-900 bg-zinc-900 text-white"
                    : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-400"
                }`}
              >
                {t.label}
                <span className="block text-[10px] opacity-70 mt-0.5">{t.credits} credits</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <Label htmlFor="topic">Topic / focus (optional)</Label>
          <Input
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. AI tools released this week"
            className="mt-1"
          />
        </div>

        <div>
          <Label htmlFor="instructions">Additional instructions (optional)</Label>
          <Textarea
            id="instructions"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="e.g. Focus on practical takeaways, include 3 examples, keep it under 800 words"
            rows={3}
            className="mt-1"
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="text-sm text-zinc-500">
            Cost: <span className="font-medium text-zinc-900">{selectedType?.credits} credits</span>
            {balance !== null && (
              <> · Balance: <span className={balance < (selectedType?.credits || 10) ? "text-red-600 font-medium" : "font-medium text-zinc-900"}>{balance}</span></>
            )}
          </div>
          <Button
            onClick={handleGenerate}
            disabled={loading || (balance !== null && balance < (selectedType?.credits || 10))}
          >
            {loading ? "Generating..." : "Generate →"}
          </Button>
        </div>

        {error && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-3">
            {error}
          </div>
        )}

        {loading && (
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-zinc-900 border-t-transparent" />
                <div>
                  <p className="text-sm font-medium">Claude is working...</p>
                  <p className="text-xs text-zinc-500 mt-0.5">{progress || "Initializing..."}</p>
                </div>
                <Badge variant="secondary" className="ml-auto">{jobStatus}</Badge>
              </div>
            </CardContent>
          </Card>
        )}

        {balance !== null && balance < (selectedType?.credits || 10) && (
          <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-md p-3">
            Not enough credits.{" "}
            <a href="/dashboard/credits" className="font-medium underline">Buy more →</a>
          </div>
        )}
      </div>
    </div>
  );
}
