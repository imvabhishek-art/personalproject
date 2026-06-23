"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

const CONTENT_TYPES = ["newsletter", "blog", "linkedin", "twitter_thread", "summary"];
const TONES = ["professional", "conversational", "witty", "authoritative"];
const PERSONAS = ["individual creator", "brand", "agency"];

const TOTAL_STEPS = 6;

export default function OnboardingPage() {
  const router = useRouter();
  const { workspaces, fetchWorkspaces } = useAuthStore();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [profile, setProfile] = useState({
    content_types: [] as string[],
    audience: "",
    persona: "",
    tone: "professional",
    topics: [] as string[],
    brand_name: "",
    writing_style: "",
  });
  const [topicInput, setTopicInput] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceSlug, setWorkspaceSlug] = useState("");

  const toggleContentType = (t: string) => {
    setProfile((p) => ({
      ...p,
      content_types: p.content_types.includes(t)
        ? p.content_types.filter((c) => c !== t)
        : [...p.content_types, t],
    }));
  };

  const addTopic = () => {
    const t = topicInput.trim();
    if (t && !profile.topics.includes(t) && profile.topics.length < 10) {
      setProfile((p) => ({ ...p, topics: [...p.topics, t] }));
      setTopicInput("");
    }
  };

  const removeTopic = (t: string) => {
    setProfile((p) => ({ ...p, topics: p.topics.filter((x) => x !== t) }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      let wsId: string;

      if (workspaces.length === 0) {
        const slug = workspaceSlug || workspaceName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
        const { data: ws } = await api.post("/workspaces", { name: workspaceName, slug });
        wsId = ws.id;
        await fetchWorkspaces();
      } else {
        wsId = workspaces[0].id;
      }

      await api.post(`/workspaces/${wsId}/onboarding`, profile);
      router.push("/dashboard");
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to save settings.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-zinc-900">Set up your workspace</h1>
          <p className="text-zinc-500 mt-2">Help us personalize every piece of content for you</p>
          <div className="flex gap-1.5 mt-6 justify-center">
            {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
              <div
                key={i}
                className={`h-1.5 w-12 rounded-full transition-colors ${
                  i < step ? "bg-zinc-900" : "bg-zinc-200"
                }`}
              />
            ))}
          </div>
        </div>

        <Card>
          <CardContent className="pt-6">
            {error && (
              <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-3">
                {error}
              </div>
            )}

            {step === 1 && (
              <div>
                <h2 className="text-lg font-semibold mb-1">Name your workspace</h2>
                <p className="text-sm text-zinc-500 mb-4">This is your team or brand workspace.</p>
                <div className="space-y-3">
                  <div>
                    <Label>Workspace name</Label>
                    <Input
                      value={workspaceName}
                      onChange={(e) => {
                        setWorkspaceName(e.target.value);
                        setWorkspaceSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""));
                      }}
                      placeholder="My Newsletter"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Slug (URL identifier)</Label>
                    <Input
                      value={workspaceSlug}
                      onChange={(e) => setWorkspaceSlug(e.target.value)}
                      placeholder="my-newsletter"
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 2 && (
              <div>
                <h2 className="text-lg font-semibold mb-1">What will you generate?</h2>
                <p className="text-sm text-zinc-500 mb-4">Select all that apply.</p>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {CONTENT_TYPES.map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => toggleContentType(type)}
                      className={`px-4 py-3 rounded-lg border text-sm font-medium transition-all capitalize ${
                        profile.content_types.includes(type)
                          ? "border-zinc-900 bg-zinc-900 text-white"
                          : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-400"
                      }`}
                    >
                      {type.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {step === 3 && (
              <div>
                <h2 className="text-lg font-semibold mb-1">Who is your audience?</h2>
                <p className="text-sm text-zinc-500 mb-4">Describe your readers or viewers.</p>
                <Textarea
                  value={profile.audience}
                  onChange={(e) => setProfile((p) => ({ ...p, audience: e.target.value }))}
                  placeholder="e.g. B2B SaaS founders and product managers interested in AI tools"
                  rows={4}
                />
              </div>
            )}

            {step === 4 && (
              <div>
                <h2 className="text-lg font-semibold mb-1">Who are you?</h2>
                <p className="text-sm text-zinc-500 mb-4">Select your persona.</p>
                <div className="grid grid-cols-3 gap-2">
                  {PERSONAS.map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setProfile((prev) => ({ ...prev, persona: p }))}
                      className={`px-4 py-3 rounded-lg border text-sm font-medium transition-all capitalize ${
                        profile.persona === p
                          ? "border-zinc-900 bg-zinc-900 text-white"
                          : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-400"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
                <p className="text-zinc-500 mt-4 mb-2 text-sm">Tone</p>
                <div className="grid grid-cols-2 gap-2">
                  {TONES.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setProfile((prev) => ({ ...prev, tone: t }))}
                      className={`px-4 py-3 rounded-lg border text-sm font-medium transition-all capitalize ${
                        profile.tone === t
                          ? "border-zinc-900 bg-zinc-900 text-white"
                          : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-400"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {step === 5 && (
              <div>
                <h2 className="text-lg font-semibold mb-1">What topics do you cover?</h2>
                <p className="text-sm text-zinc-500 mb-4">Add up to 10 topics.</p>
                <div className="flex gap-2">
                  <Input
                    value={topicInput}
                    onChange={(e) => setTopicInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addTopic())}
                    placeholder="e.g. AI, SaaS, Product Management"
                  />
                  <Button type="button" variant="outline" onClick={addTopic}>Add</Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {profile.topics.map((t) => (
                    <span
                      key={t}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-zinc-100 text-zinc-800 rounded-full text-sm"
                    >
                      {t}
                      <button type="button" onClick={() => removeTopic(t)} className="text-zinc-400 hover:text-zinc-600">×</button>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {step === 6 && (
              <div>
                <h2 className="text-lg font-semibold mb-1">Brand & style (optional)</h2>
                <p className="text-sm text-zinc-500 mb-4">Give Claude more context about your brand.</p>
                <div className="space-y-3">
                  <div>
                    <Label>Brand name</Label>
                    <Input
                      value={profile.brand_name}
                      onChange={(e) => setProfile((p) => ({ ...p, brand_name: e.target.value }))}
                      placeholder="e.g. The AI Weekly"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Writing style notes</Label>
                    <Textarea
                      value={profile.writing_style}
                      onChange={(e) => setProfile((p) => ({ ...p, writing_style: e.target.value }))}
                      placeholder="e.g. Use bullet points, avoid jargon, include data-backed insights"
                      rows={3}
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="mt-4 flex justify-between">
          <Button
            variant="outline"
            onClick={() => setStep((s) => Math.max(1, s - 1))}
            disabled={step === 1}
          >
            Back
          </Button>
          {step < TOTAL_STEPS ? (
            <Button onClick={() => setStep((s) => s + 1)}>
              Continue
            </Button>
          ) : (
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? "Saving..." : "Finish setup"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
