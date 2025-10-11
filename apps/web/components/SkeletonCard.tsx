"use client";
export function SkeletonCard() {
  return (
    <div className="card animate-pulse">
      <div className="card-head flex items-center gap-3">
        <div className="badge w-16">&nbsp;</div>
        <div className="h-5 w-52 rounded bg-slate-200 dark:bg-white/10" />
      </div>
      <div className="card-body space-y-4">
        <div className="h-40 w-full rounded bg-slate-200 dark:bg-white/10" />
        <div className="h-3 w-4/5 rounded bg-slate-200 dark:bg-white/10" />
        <div className="h-3 w-3/5 rounded bg-slate-200 dark:bg-white/10" />
      </div>
    </div>
  );
}

