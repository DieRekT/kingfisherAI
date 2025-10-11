import { NextRequest } from "next/server";
import { openai } from "@ai-sdk/openai";
import { generateObject } from "ai";
import { z } from "zod";

// Simplified agent route using generateObject instead of @openai/agents
// The @openai/agents package has peer dependency conflicts with zod v4

const AgentCardSchema = z.object({
  title: z.string(),
  summary: z.string(),
  steps: z.array(z.string()),
  image_url: z.string().url().optional(),
});

export async function POST(req: NextRequest) {
  const { prompt } = await req.json();

  // Generate image suggestion first
  const query = encodeURIComponent(prompt.split(" ").slice(0, 3).join(" "));
  const suggestedImageUrl = `https://source.unsplash.com/featured/?${query}`;

  const result = await generateObject({
    model: openai("gpt-4o-mini"),
    schema: AgentCardSchema,
    prompt: `Create a compact, factual card about: ${prompt}
    
Include practical steps and use this image URL if relevant: ${suggestedImageUrl}
Output compact, factual content suitable for a teaching card.`,
  });

  return new Response(
    JSON.stringify({
      finalOutput: result.object,
      attribution: "Unsplash featured",
    }),
    {
      headers: { "content-type": "application/json" },
    }
  );
}

