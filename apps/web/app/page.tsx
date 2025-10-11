"use client";
import * as React from "react";
import { LessonCard } from "../components/LessonCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { ToastContainer } from "../components/Toast";
import { PINNED_DEMOS } from "./pinnedPrompts";
import { useToast } from "./useToast";

type ChatResult = {
  text?: string;
  model?: string;
  tool_calls?: string[];
  lesson_cards?: any[]; // server shape; card mapper below will normalize
};

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function Page() {
  const [input, setInput] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<ChatResult | null>(null);
  const { toasts, toast, dismissToast } = useToast();

  async function send() {
    setError(null);
    if (!input.trim()) return;
    setLoading(true);
    try {
      // Prefer streaming (works with your API)
      const es = new EventSource(`${apiBase}/api/chat/stream?q=${encodeURIComponent(input)}`);
      es.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type === "result") {
            setResult(msg.payload);
            setLoading(false);
            es.close();
            toast.success("Response complete!");
          }
        } catch (_) {}
      };
      es.onerror = () => {
        es.close();
        setLoading(false);
        const errorMsg = "Connection error. Check if API is running on port 8000.";
        setError(errorMsg);
        toast.error(errorMsg);
      };
    } catch {
      // Fallback to POST if EventSource fails (rare)
      try {
        const res = await fetch(`${apiBase}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: input }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setResult(await res.json());
        toast.success("Response complete!");
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Failed to connect";
        setError(errorMsg);
        toast.error(errorMsg);
      } finally {
        setLoading(false);
      }
    }
  }

  // Handle demo button click
  function loadDemo(prompt: string) {
    setInput(prompt);
    // Auto-send after short delay
    setTimeout(() => {
      const sendButton = document.querySelector('button[type="button"]') as HTMLButtonElement;
      sendButton?.click();
    }, 100);
  }

  // Normalize server cards to the LessonCard shape
  const cards = React.useMemo(() => {
    const raw = result?.lesson_cards ?? [];
    return raw.map((c: any) => ({
      title: c.title,
      kind: c.kind ?? "howto",
      steps: (c.steps ?? []).map((s: any) => ({ title: s.title ?? String(s), body: s.body })),
      image: c.image
        ? {
            url: c.image.url,
            alt: c.image.alt,
            credit: c.image.credit,
            href: c.image.href,
          }
        : undefined,
      citations: c.citations,
    }));
  }, [result]);

  return (
    <>
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      <main className="container-app py-6 sm:py-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight">Kingfisher 2465</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
            Ask anything. Get concise chat + beautiful lesson cards.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <span className="kbd">⌘</span><span>+</span><span className="kbd">Enter</span>
        </div>
      </div>

      {/* Pinned Demo Prompts */}
      <div className="mb-6 overflow-x-auto">
        <div className="flex gap-2 pb-2">
          {PINNED_DEMOS.slice(0, 8).map((demo) => (
            <button
              key={demo.id}
              onClick={() => loadDemo(demo.prompt)}
              disabled={loading}
              className="shrink-0 px-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={demo.prompt}
            >
              {demo.label}
            </button>
          ))}
        </div>
      </div>

      {/* Layout: chat left, cards right */}
      <div className="grid gap-6 lg:grid-cols-[420px_minmax(0,1fr)]">
        {/* Chat pane */}
        <section className="card h-[70vh] lg:h-[76vh] flex flex-col">
          <div className="card-head">
            <div className="text-sm text-slate-500 dark:text-slate-400">
              Model: <span className="font-medium">{result?.model ?? "…"}</span>
            </div>
          </div>
          <div className="card-body grow overflow-auto">
            {result?.text ? (
              <article className="prose prose-slate dark:prose-invert max-w-none">
                {result.text.split("\n").map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </article>
            ) : (
              <div className="h-full grid place-items-center text-slate-400">
                <div>Start a conversation…</div>
              </div>
            )}
          </div>

          <div className="border-t border-slate-200 px-4 py-3 dark:border-white/10">
            <div className="flex items-center gap-2">
              <input
                className="input"
                placeholder="Ask Kingfisher…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => (e.key === "Enter" && (e.metaKey || e.ctrlKey)) ? send() : undefined}
              />
              <button type="button" className="btn" onClick={send} disabled={loading}>
                {loading ? "Thinking…" : "Ask"}
              </button>
            </div>
            {error ? <p className="mt-2 text-xs text-red-600">{error}</p> : null}
          </div>
        </section>

        {/* Cards pane */}
        <section className="min-h-[70vh] lg:h-[76vh] overflow-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {loading && !cards.length ? (
              <>
                <SkeletonCard />
                <SkeletonCard />
              </>
            ) : null}
            {cards.map((card, i) => <LessonCard key={i} card={card} />)}
          </div>
        </section>
      </div>
    </main>
    </>
  );
}
