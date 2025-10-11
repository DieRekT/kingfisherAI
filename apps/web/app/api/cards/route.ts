import { NextRequest } from "next/server";
import { z } from "zod";
import { openai } from "@ai-sdk/openai";
import { generateObject } from "ai";

export const runtime = "nodejs";

const CardSchema = z.object({
  id: z.string(),
  title: z.string().max(120),
  summary: z.string().max(400),
  steps: z.array(z.string()).min(1).max(12),
  image_url: z.string().url().optional(),
  tags: z.array(z.string()).max(10).optional(),
  cta: z.object({ label: z.string(), href: z.string().url() }).optional(),
});
const CardListSchema = z.object({ cards: z.array(CardSchema).min(1).max(12) });

export async function POST(req: NextRequest) {
  const { topic } = await req.json();

  const result = await generateObject({
    model: openai("gpt-4o-mini"),
    schema: CardListSchema,
    prompt: `You format content into concise UI cards for busy professionals.
Topic: ${topic}
Return a diverse set of cards with practical steps. Include image_url only if a broadly reusable, trustworthy image is available.`,
  });

  return new Response(JSON.stringify(result.object), {
    headers: { "content-type": "application/json" },
  });
}

