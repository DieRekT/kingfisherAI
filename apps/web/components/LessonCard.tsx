"use client";
import * as React from "react";
import { ImageWithCredit } from "./ImageWithCredit";
import { StepItem } from "./StepItem";

type Step = { title: string; body?: string };
type Card = {
  title: string;
  kind: "howto" | "concept" | "plan" | "reference";
  steps?: Step[];
  image?: { url?: string; credit?: string; href?: string; alt?: string };
  citations?: { title: string; url: string }[];
};

const kindLabel: Record<Card["kind"], string> = {
  howto: "How-to",
  concept: "Concept",
  plan: "Plan",
  reference: "Reference",
};

export function LessonCard({ card }: { card: Card }) {
  const hasImage = Boolean(card?.image?.url);
  return (
    <article className="card">
      <header className="card-head flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="badge">{kindLabel[card.kind] || "Card"}</span>
          <h3 className="text-base sm:text-lg font-semibold leading-7">{card.title}</h3>
        </div>
      </header>

      <div className="card-body space-y-5">
        <div className={hasImage ? "grid gap-5 md:grid-cols-2" : ""}>
          {hasImage && (
            <div className="order-last md:order-first">
              <ImageWithCredit
                src={card.image?.url}
                alt={card.image?.alt}
                credit={card.image?.credit}
                href={card.image?.href}
              />
            </div>
          )}

          {card.steps?.length ? (
            <ol className="space-y-4">
              {card.steps.map((s, i) => (
                <StepItem key={i} index={i} title={s.title} body={s.body} />
              ))}
            </ol>
          ) : (
            <p className="text-sm text-slate-600 dark:text-slate-300">No steps provided.</p>
          )}
        </div>

        {card.citations?.length ? (
          <div className="flex flex-wrap gap-2 pt-2">
            {card.citations.slice(0, 6).map((c, i) => (
              <a
                key={i}
                className="badge hover:opacity-90"
                href={c.url}
                target="_blank"
                rel="noreferrer"
                title={c.title}
              >
                {new URL(c.url).hostname.replace(/^www\./, "")}
              </a>
            ))}
          </div>
        ) : null}
      </div>
    </article>
  );
}

