"use client";
import * as React from "react";

export function StepItem({
  index,
  title,
  body,
}: {
  index: number;
  title: string;
  body?: string;
}) {
  return (
    <li className="grid grid-cols-[auto_1fr] gap-3">
      <div className="mt-1 h-6 w-6 shrink-0 rounded-full bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-xs grid place-items-center">
        {index + 1}
      </div>
      <div>
        <div className="font-medium leading-6">{title}</div>
        {body ? <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">{body}</p> : null}
      </div>
    </li>
  );
}

