/**
 * GET /api/docs - List all ingested documents
 */
import { NextResponse } from "next/server";
import { listDocs } from "@/lib/rag/registry";

export async function GET() {
  try {
    const docs = await listDocs();
    return NextResponse.json({ docs });
  } catch (error) {
    console.error("List docs error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to list documents" },
      { status: 500 }
    );
  }
}

