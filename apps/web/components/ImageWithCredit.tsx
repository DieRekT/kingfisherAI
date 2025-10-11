"use client";
import * as React from "react";

export function ImageWithCredit({
  src,
  alt,
  credit,
  href,
}: {
  src?: string;
  alt?: string;
  credit?: string;
  href?: string;
}) {
  return (
    <figure className="overflow-hidden rounded-xl border border-slate-200 dark:border-white/10">
      <div className="aspect-video bg-slate-100 dark:bg-white/5">
        {src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={src} alt={alt || ""} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-slate-400">
            No image
          </div>
        )}
      </div>
      {(credit || href) && (
        <figcaption className="flex items-center justify-between gap-3 px-3 py-2 text-xs text-slate-500 dark:text-slate-400">
          <span className="truncate">{credit}</span>
          {href && (
            <a
              className="underline decoration-dotted underline-offset-2 hover:text-slate-700 dark:hover:text-slate-200"
              href={href}
              target="_blank"
              rel="noreferrer"
            >
              Source
            </a>
          )}
        </figcaption>
      )}
    </figure>
  );
}

