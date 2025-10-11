/**
 * DELETE /api/docs/[docId] - Delete document by ID
 */
import { NextRequest, NextResponse } from "next/server";
import fs from "fs/promises";
import { deleteByDocId } from "@/lib/rag/store";
import { removeDoc, getDoc } from "@/lib/rag/registry";

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { docId: string } }
) {
  try {
    const { docId } = params;

    // Get doc entry to find file path
    const doc = await getDoc(docId);

    if (!doc) {
      return NextResponse.json({ error: "Document not found" }, { status: 404 });
    }

    // Delete vectors from LanceDB
    await deleteByDocId(docId);

    // Delete physical file
    try {
      await fs.unlink(doc.filePath);
    } catch (error) {
      console.warn(`File deletion failed for ${doc.filePath}:`, error);
    }

    // Remove from registry
    await removeDoc(docId);

    return NextResponse.json({
      message: "Document deleted",
      docId,
      filename: doc.filename,
    });
  } catch (error) {
    console.error("Delete doc error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to delete document" },
      { status: 500 }
    );
  }
}

