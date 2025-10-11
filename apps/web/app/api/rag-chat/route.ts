/**
 * POST /api/rag-chat - RAG-powered chat with citations
 */
import { NextRequest } from "next/server";
import { openai } from "@ai-sdk/openai";
import { streamText } from "ai";
import { embed } from "@/lib/rag/embeddings";
import { search } from "@/lib/rag/store";

const TOP_K = parseInt(process.env.RAG_TOP_K || "6", 10);

export const maxDuration = 60;

export async function POST(req: NextRequest) {
  try {
    const { q } = await req.json();

    if (!q || typeof q !== "string") {
      return new Response(JSON.stringify({ error: "Query 'q' is required" }), {
        status: 400,
        headers: { "content-type": "application/json" },
      });
    }

    // Retrieve context
    const queryVector = await embed(q);
    const results = await search(queryVector, TOP_K);

    // Build context with source labels
    const contextParts = results.map((r, idx) => {
      return `[S${idx + 1}] (${r.filename}, chunk ${r.chunkIndex}):\n${r.text}`;
    });

    const context = contextParts.join("\n\n---\n\n");

    // Build sources list
    const sources = results.map((r, idx) => ({
      label: `S${idx + 1}`,
      filename: r.filename,
      chunkIndex: r.chunkIndex,
    }));

    // Stream answer
    const result = streamText({
      model: openai("gpt-4o-mini"),
      system: `You are a precise assistant that answers questions using ONLY the provided context.

RULES:
1. Base your answer strictly on the context below.
2. Reference sources using [S1], [S2], etc. inline when you cite information.
3. If the context doesn't contain the answer, say "I don't have enough information in the provided documents."
4. Be concise and factual.

CONTEXT:
${context}`,
      messages: [{ role: "user", content: q }],
    });

    // Prepend sources metadata to stream
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        // Send sources metadata first
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({ type: "sources", sources })}\n\n`
          )
        );

        // Stream AI response
        const reader = result.toTextStreamResponse().body?.getReader();
        if (!reader) throw new Error("No stream reader");

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          controller.enqueue(value);
        }

        controller.close();
      },
    });

    return new Response(stream, {
      headers: {
        "content-type": "text/event-stream",
        "cache-control": "no-cache",
        connection: "keep-alive",
      },
    });
  } catch (error) {
    console.error("RAG chat error:", error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Chat failed",
      }),
      {
        status: 500,
        headers: { "content-type": "application/json" },
      }
    );
  }
}

