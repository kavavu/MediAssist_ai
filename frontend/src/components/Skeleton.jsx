import React from "react";

export function SkeletonText({ lines = 3, className = "" }) {
  return (
    <div className={`space-y-2.5 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-3 rounded-full animate-shimmer"
          style={{ width: i === lines - 1 ? "60%" : "100%" }}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ count = 1 }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full animate-shimmer" />
            <div className="flex-1 space-y-2">
              <div className="h-3.5 rounded-full animate-shimmer w-1/3" />
              <div className="h-2.5 rounded-full animate-shimmer w-1/4" />
            </div>
          </div>
          <SkeletonText lines={3} />
          <div className="flex gap-2 mt-4">
            <div className="h-8 rounded-lg animate-shimmer w-20" />
            <div className="h-8 rounded-lg animate-shimmer w-20" />
          </div>
        </div>
      ))}
    </>
  );
}

export function SkeletonTable({ rows = 5, cols = 4 }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="grid gap-4 px-5 py-3 bg-slate-50 border-b border-slate-200"
        style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}
      >
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="h-3.5 rounded-full animate-shimmer w-3/4" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, r) => (
        <div
          key={r}
          className="grid gap-4 px-5 py-3.5 border-b border-slate-100 last:border-0"
          style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}
        >
          {Array.from({ length: cols }).map((_, c) => (
            <div
              key={c}
              className="h-3 rounded-full animate-shimmer"
              style={{ width: c === 0 ? "80%" : "60%" }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonStats({ count = 4 }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="h-3 rounded-full animate-shimmer w-24" />
            <div className="w-8 h-8 rounded-lg animate-shimmer" />
          </div>
          <div className="h-8 rounded-full animate-shimmer w-16 mb-1" />
          <div className="h-2.5 rounded-full animate-shimmer w-20" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonPills({ count = 5 }) {
  return (
    <div className="flex flex-wrap gap-2">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="h-7 rounded-full animate-shimmer"
          style={{ width: `${60 + Math.random() * 60}px` }}
        />
      ))}
    </div>
  );
}
