/**
 * OpenAI embeddings wrapper
 */
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const EMBED_MODEL = process.env.RAG_EMBED_MODEL || "text-embedding-3-large";
export const EMBED_DIMENSION = 3072; // text-embedding-3-large dimension

export async function embed(text: string): Promise<number[]> {
  try {
    const response = await openai.embeddings.create({
      model: EMBED_MODEL,
      input: text,
    });

    const embedding = response.data[0]?.embedding;
    if (!embedding) {
      throw new Error("No embedding returned from API");
    }

    return embedding;
  } catch (error) {
    throw new Error(`Embedding failed: ${error instanceof Error ? error.message : String(error)}`);
  }
}

export async function embedBatch(texts: string[]): Promise<number[][]> {
  try {
    const response = await openai.embeddings.create({
      model: EMBED_MODEL,
      input: texts,
    });

    return response.data.map((item) => item.embedding);
  } catch (error) {
    throw new Error(`Batch embedding failed: ${error instanceof Error ? error.message : String(error)}`);
  }
}

