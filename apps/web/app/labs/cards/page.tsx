'use client';
import { useState } from "react";
import { useChat } from "@ai-sdk/react";
import CardGrid from "@/components/CardGrid";
import clsx from "clsx";
import type { CardData } from "@/ai/types";

export default function Page() {
  const [inputValue, setInputValue] = useState('Make 2 cards on "Next.js security basics" with steps and one image.');
  const [cards, setCards] = useState<CardData[]>([]);

  const { messages, sendMessage, status } = useChat();

  const isLoading = status === "submitted";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCards([]);
    await sendMessage({
      parts: [
        {
          type: "text",
          text: inputValue,
        },
      ],
    });
  };

  // Extract assistant messages
  const assistantMessages = messages
    .flatMap((m) => m.parts)
    .filter((p) => p.type === "text")
    .map((p: any) => p.text)
    .join("\n");

  return (
    <main className="mx-auto max-w-5xl p-4 space-y-6">
      <h1 className="text-2xl font-bold">KingfisherAI — Cards Lab</h1>
      <section className="rounded-2xl border bg-white p-4 shadow-sm space-y-3">
        <form className="flex gap-2" onSubmit={handleSubmit}>
          <input
            className="flex-1 rounded-xl border px-3 py-2"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask for cards…"
          />
          <button
            className={clsx(
              "rounded-xl px-4 py-2 text-white",
              isLoading ? "bg-gray-400" : "bg-gray-900"
            )}
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? "Generating…" : "Send"}
          </button>
        </form>
        <div className="text-sm text-neutral-600 whitespace-pre-wrap">
          {assistantMessages}
        </div>
      </section>

      {!!cards.length && (
        <section className="space-y-2">
          <h2 className="text-lg font-semibold">Cards</h2>
          <CardGrid cards={cards} />
        </section>
      )}
      
      <section className="mt-4 text-sm text-neutral-500">
        <p>
          💡 This is a demo of AI SDK v5 streaming. The cards route (<code>/api/cards</code>) uses{" "}
          <code>generateObject</code> for structured outputs.
        </p>
      </section>
    </main>
  );
}

