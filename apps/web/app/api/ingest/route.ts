/**
 * POST /api/ingest - File ingestion endpoint
 * Accepts multipart form data with files
 */
import { NextRequest, NextResponse } from "next/server";
import { v4 as uuidv4 } from "uuid";
import fs from "fs/promises";
import path from "path";
import { extractText } from "@/lib/rag/extract";
import { chunkText } from "@/lib/rag/chunk";
import { embedBatch } from "@/lib/rag/embeddings";
import { addVectors } from "@/lib/rag/store";
import { addDoc } from "@/lib/rag/registry";

const RAG_DATA_DIR = process.env.RAG_DATA_DIR || "data/rag";
const LIBRARY_DIR = path.join(process.cwd(), RAG_DATA_DIR, "library");

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const files = formData.getAll("files") as File[];

    if (!files || files.length === 0) {
      return NextResponse.json({ error: "No files provided" }, { status: 400 });
    }

    // Ensure library directory exists
    await fs.mkdir(LIBRARY_DIR, { recursive: true });

    const results = [];

    for (const file of files) {
      const docId = uuidv4();
      const buffer = Buffer.from(await file.arrayBuffer());
      const filename = file.name;

      // Save original file
      const filePath = path.join(LIBRARY_DIR, `${docId}_${filename}`);
      await fs.writeFile(filePath, buffer);

      try {
        // Extract text
        const text = await extractText(buffer, filename);

        // Chunk text
        const chunks = chunkText(text, docId);

        // Embed chunks
        const embeddings = await embedBatch(chunks.map((c) => c.text));

        // Prepare vector rows
        const vectorRows = chunks.map((chunk, idx) => ({
          docId,
          chunkIndex: chunk.index,
          text: chunk.text,
          vector: embeddings[idx] || [],
          filename,
        }));

        // Store in LanceDB
        await addVectors(vectorRows);

        // Update registry
        await addDoc({
          docId,
          filename,
          uploadedAt: new Date().toISOString(),
          chunks: chunks.length,
          filePath,
        });

        results.push({
          docId,
          filename,
          chunks: chunks.length,
          status: "success",
        });
      } catch (error) {
        // Clean up file on processing failure
        await fs.unlink(filePath).catch(() => {});
        results.push({
          filename,
          status: "error",
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    return NextResponse.json({
      message: "Ingestion complete",
      results,
    });
  } catch (error) {
    console.error("Ingest error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Ingestion failed" },
      { status: 500 }
    );
  }
}

