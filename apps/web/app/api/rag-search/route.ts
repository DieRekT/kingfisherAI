/**
 * POST /api/rag-search - Semantic search
 */
import { NextRequest, NextResponse } from "next/server";
import { embed } from "@/lib/rag/embeddings";
import { search } from "@/lib/rag/store";

const TOP_K = parseInt(process.env.RAG_TOP_K || "6", 10);

export async function POST(req: NextRequest) {
  try {
    const { q } = await req.json();

    if (!q || typeof q !== "string") {
      return NextResponse.json({ error: "Query 'q' is required" }, { status: 400 });
    }

    // Embed query
    const queryVector = await embed(q);

    // Search vectors
    const results = await search(queryVector, TOP_K);

    return NextResponse.json({
      query: q,
      results: results.map((r, idx) => ({
        source: `S${idx + 1}`,
        docId: r.docId,
        filename: r.filename,
        chunkIndex: r.chunkIndex,
        text: r.text,
        score: r.score,
      })),
    });
  } catch (error) {
    console.error("RAG search error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Search failed" },
      { status: 500 }
    );
  }
}

