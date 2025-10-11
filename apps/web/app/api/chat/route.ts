import { openai } from "@ai-sdk/openai";
import { streamText } from "ai";

export const maxDuration = 60;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai("gpt-4o-mini"),
    system:
      "You are precise. When appropriate, describe the cards you would create with their titles, summaries, and step-by-step instructions. Keep your explanations clear and actionable.",
    messages,
  });

  return result.toTextStreamResponse();
}

