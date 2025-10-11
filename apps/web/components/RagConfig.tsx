'use client';

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface RagConfigProps {
  onConfigChange?: (config: RagConfigValues) => void;
}

export interface RagConfigValues {
  maxChunkTokens: number;
  topK: number;
  embedModel: string;
}

const DEFAULT_CONFIG: RagConfigValues = {
  maxChunkTokens: 900,
  topK: 6,
  embedModel: "text-embedding-3-large",
};

export function RagConfig({ onConfigChange }: RagConfigProps) {
  const [config, setConfig] = useState<RagConfigValues>(DEFAULT_CONFIG);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleUpdate = (key: keyof RagConfigValues, value: string | number) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    onConfigChange?.(newConfig);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">RAG Configuration</CardTitle>
            <CardDescription>
              Customize chunk sizes and retrieval settings
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? "Hide" : "Show"}
          </Button>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-4">
          {/* Chunk Size */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center justify-between">
              <span>Max Chunk Tokens</span>
              <span className="text-muted-foreground font-normal">
                {config.maxChunkTokens}
              </span>
            </label>
            <Input
              type="range"
              min="300"
              max="1500"
              step="50"
              value={config.maxChunkTokens}
              onChange={(e) => handleUpdate("maxChunkTokens", parseInt(e.target.value))}
              className="cursor-pointer"
            />
            <p className="text-xs text-muted-foreground">
              Smaller chunks (300-600): More granular, precise results<br />
              Larger chunks (900-1500): More context, broader answers
            </p>
          </div>

          {/* Top K */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center justify-between">
              <span>Top K Results</span>
              <span className="text-muted-foreground font-normal">
                {config.topK}
              </span>
            </label>
            <Input
              type="range"
              min="1"
              max="20"
              step="1"
              value={config.topK}
              onChange={(e) => handleUpdate("topK", parseInt(e.target.value))}
              className="cursor-pointer"
            />
            <p className="text-xs text-muted-foreground">
              Number of relevant chunks to retrieve for each query
            </p>
          </div>

          {/* Embedding Model */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Embedding Model</label>
            <select
              value={config.embedModel}
              onChange={(e) => handleUpdate("embedModel", e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="text-embedding-3-large">text-embedding-3-large (3072 dims)</option>
              <option value="text-embedding-3-small">text-embedding-3-small (1536 dims)</option>
            </select>
            <p className="text-xs text-muted-foreground">
              Note: Changing model requires re-ingesting all documents
            </p>
          </div>

          {/* Info Box */}
          <div className="mt-4 rounded-lg bg-muted p-3">
            <p className="text-xs text-muted-foreground">
              <strong>Note:</strong> These settings are client-side preferences. 
              To persist changes, update your <code className="bg-background px-1 py-0.5 rounded">.env.local</code> file:
            </p>
            <pre className="mt-2 text-xs bg-background p-2 rounded overflow-x-auto">
{`RAG_MAX_CHUNK_TOKENS=${config.maxChunkTokens}
RAG_TOP_K=${config.topK}
RAG_EMBED_MODEL=${config.embedModel}`}
            </pre>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

