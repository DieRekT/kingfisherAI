/**
 * Token-aware chunking with safe fallback
 */
import { encodingForModel } from "js-tiktoken";

const MAX_CHUNK_TOKENS = parseInt(process.env.RAG_MAX_CHUNK_TOKENS || "900", 10);
const OVERLAP_TOKENS = 100;

export interface Chunk {
  text: string;
  index: number;
}

export function chunkText(text: string, docId: string): Chunk[] {
  try {
    const encoding = encodingForModel("gpt-4");
    const tokens = encoding.encode(text);
    const chunks: Chunk[] = [];
    let index = 0;

    for (let i = 0; i < tokens.length; i += MAX_CHUNK_TOKENS - OVERLAP_TOKENS) {
      const chunkTokens = tokens.slice(i, i + MAX_CHUNK_TOKENS);
      const decoded = encoding.decode(chunkTokens);
      const chunkText = typeof decoded === 'string' ? decoded : new TextDecoder().decode(decoded as any);
      
      chunks.push({
        text: chunkText.trim(),
        index: index++,
      });
    }

    return chunks.length > 0 ? chunks : [{ text: text.slice(0, 3000), index: 0 }];

  } catch (error) {
    // Safe fallback: character-based chunking
    console.warn(`Token encoding failed for ${docId}, using char-based chunking:`, error);
    return fallbackChunk(text);
  }
}

function fallbackChunk(text: string): Chunk[] {
  const CHAR_CHUNK_SIZE = 3000;
  const CHAR_OVERLAP = 300;
  const chunks: Chunk[] = [];
  let index = 0;

  for (let i = 0; i < text.length; i += CHAR_CHUNK_SIZE - CHAR_OVERLAP) {
    const chunkText = text.slice(i, i + CHAR_CHUNK_SIZE);
    chunks.push({
      text: chunkText.trim(),
      index: index++,
    });
  }

  return chunks.length > 0 ? chunks : [{ text: text.slice(0, 3000), index: 0 }];
}

