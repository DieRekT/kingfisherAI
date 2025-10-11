'use client';
import { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RagConfig } from "@/components/RagConfig";

interface Doc {
  docId: string;
  filename: string;
  uploadedAt: string;
  chunks: number;
}

interface SearchResult {
  source: string;
  filename: string;
  text: string;
  score: number;
}

interface Source {
  label: string;
  filename: string;
  chunkIndex: number;
}

export default function DropzonePage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [chatQuery, setChatQuery] = useState("");
  const [chatAnswer, setChatAnswer] = useState("");
  const [chatSources, setChatSources] = useState<Source[]>([]);
  const [uploading, setUploading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [chatting, setChatting] = useState(false);

  const loadDocs = useCallback(async () => {
    try {
      const res = await fetch("/api/docs");
      const data = await res.json();
      setDocs(data.docs || []);
    } catch (error) {
      console.error("Failed to load docs:", error);
    }
  }, []);

  useEffect(() => {
    loadDocs();
  }, [loadDocs]);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    try {
      const formData = new FormData();
      Array.from(files).forEach((file) => {
        formData.append("files", file);
      });

      const res = await fetch("/api/ingest", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");

      await loadDocs();
      alert("Files ingested successfully!");
    } catch (error) {
      console.error("Upload error:", error);
      alert(`Upload failed: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm("Delete this document?")) return;

    try {
      const res = await fetch(`/api/docs/${docId}`, {
        method: "DELETE",
      });

      if (!res.ok) throw new Error("Delete failed");

      await loadDocs();
    } catch (error) {
      console.error("Delete error:", error);
      alert(`Delete failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    setSearchResults([]);

    try {
      const res = await fetch("/api/rag-search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ q: searchQuery }),
      });

      if (!res.ok) throw new Error("Search failed");

      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error("Search error:", error);
      alert(`Search failed: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setSearching(false);
    }
  };

  const handleChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatQuery.trim()) return;

    setChatting(true);
    setChatAnswer("");
    setChatSources([]);

    try {
      const res = await fetch("/api/rag-chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ q: chatQuery }),
      });

      if (!res.ok) throw new Error("Chat failed");

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No stream reader");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6);
            if (dataStr === "[DONE]") continue;

            try {
              const data = JSON.parse(dataStr);
              
              if (data.type === "sources") {
                setChatSources(data.sources);
              } else if (data.type === "0" && data.value) {
                // Text delta from AI SDK stream
                setChatAnswer((prev) => prev + data.value);
              } else if (typeof data === "string") {
                // Plain text chunk
                setChatAnswer((prev) => prev + data);
              }
            } catch {
              // Plain text line
              setChatAnswer((prev) => prev + dataStr);
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      alert(`Chat failed: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setChatting(false);
    }
  };

  return (
    <main className="mx-auto max-w-6xl p-4 space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">RAG Dropzone</h1>
        <p className="text-muted-foreground">
          Upload PDFs/DOCX/HTML/TXT/MD → Semantic search → Chat with citations
        </p>
      </header>

      {/* Configuration Section */}
      <RagConfig />

      {/* File Upload */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Drag and drop files or click to browse
          </CardDescription>
        </CardHeader>
        <CardContent>
          <label
            className={`flex items-center justify-center border-2 border-dashed rounded-lg p-8 cursor-pointer transition ${
              uploading ? "border-muted bg-muted/50" : "border-border hover:border-primary hover:bg-accent/50"
            }`}
          >
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.html,.htm,.txt,.md"
              className="hidden"
              onChange={(e) => handleFileUpload(e.target.files)}
              disabled={uploading}
            />
            <div className="text-center">
              <p className="text-lg font-medium">
                {uploading ? "Uploading..." : "Drop files or click to browse"}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                PDF, DOCX, HTML, TXT, MD
              </p>
            </div>
          </label>
        </CardContent>
      </Card>

      {/* Document List */}
      <Card>
        <CardHeader>
          <CardTitle>Documents ({docs.length})</CardTitle>
          <CardDescription>
            Uploaded and indexed documents
          </CardDescription>
        </CardHeader>
        <CardContent>
          {docs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No documents yet</p>
          ) : (
            <div className="space-y-2">
              {docs.map((doc) => (
                <div key={doc.docId} className="flex items-center justify-between border rounded-lg p-3">
                  <div className="flex-1">
                    <p className="font-medium">{doc.filename}</p>
                    <p className="text-xs text-muted-foreground">
                      {doc.chunks} chunks · {new Date(doc.uploadedAt).toLocaleString()}
                    </p>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDelete(doc.docId)}
                  >
                    Delete
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Semantic Search */}
      <Card>
        <CardHeader>
          <CardTitle>Semantic Search</CardTitle>
          <CardDescription>
            Find relevant content across all documents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2 mb-4">
            <Input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents..."
              className="flex-1"
            />
            <Button
              type="submit"
              disabled={searching}
            >
              {searching ? "Searching..." : "Search"}
            </Button>
          </form>

          {searchResults.length > 0 && (
            <div className="space-y-3">
              {searchResults.map((result, idx) => (
                <div key={idx} className="border rounded-lg p-3 bg-accent/5">
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-xs font-mono bg-muted px-2 py-1 rounded">
                      {result.source}
                    </span>
                    <span className="text-xs text-muted-foreground">{result.filename}</span>
                  </div>
                  <p className="text-sm">{result.text}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Score: {result.score.toFixed(4)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* RAG Chat */}
      <Card>
        <CardHeader>
          <CardTitle>Ask Questions</CardTitle>
          <CardDescription>
            Get AI-powered answers with citations from your documents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChat} className="flex gap-2 mb-4">
            <Input
              type="text"
              value={chatQuery}
              onChange={(e) => setChatQuery(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="flex-1"
            />
            <Button
              type="submit"
              disabled={chatting}
            >
              {chatting ? "Thinking..." : "Ask"}
            </Button>
          </form>

          {chatAnswer && (
            <div className="space-y-3">
              <div className="border rounded-lg p-4 bg-accent/10">
                <p className="text-sm whitespace-pre-wrap leading-relaxed">{chatAnswer}</p>
              </div>

              {chatSources.length > 0 && (
                <div className="border-t pt-3">
                  <p className="text-xs font-semibold text-foreground mb-2">Sources:</p>
                  <div className="space-y-1">
                    {chatSources.map((source) => (
                      <p key={source.label} className="text-xs text-muted-foreground">
                        {source.label}: {source.filename} (chunk {source.chunkIndex})
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </main>
  );
}

