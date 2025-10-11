'use client';
import Image from "next/image";

export type Card = {
  id: string;
  title: string;
  summary: string;
  steps: string[];
  image_url?: string;
  tags?: string[];
  cta?: { label: string; href: string };
};

export default function CardGrid({ cards }: { cards: Card[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map((c) => (
        <article key={c.id} className="rounded-2xl border bg-white text-black shadow-sm p-4">
          <header className="space-y-1">
            <h3 className="text-lg font-semibold">{c.title}</h3>
            <p className="text-sm text-neutral-600">{c.summary}</p>
          </header>
          {c.image_url && (
            <div className="relative mt-3 h-40 w-full overflow-hidden rounded-xl">
              <Image src={c.image_url} alt={c.title} fill className="object-cover" />
            </div>
          )}
          <ol className="mt-3 list-decimal pl-5 text-sm space-y-1">
            {c.steps.map((s, i) => <li key={i}>{s}</li>)}
          </ol>
          <footer className="mt-3 flex flex-wrap gap-2">
            {c.tags?.slice(0, 6).map((t) => (
              <span key={t} className="rounded-full border px-2 py-0.5 text-xs text-neutral-600">{t}</span>
            ))}
            {c.cta && (
              <a className="ml-auto text-sm underline" href={c.cta.href} rel="noopener noreferrer">{c.cta.label}</a>
            )}
          </footer>
        </article>
      ))}
    </div>
  );
}

