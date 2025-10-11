import type { UIMessage } from "ai";

export type CardData = {
  id: string;
  title: string;
  summary: string;
  steps: string[];
  image_url?: string;
  tags?: string[];
  cta?: { label: string; href: string };
};

export type AppUIMessage = UIMessage<
  never,
  { "data-card": CardData }
>;

