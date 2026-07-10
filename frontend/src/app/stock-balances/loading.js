// src/app/loading.js
import React from "react";

export default function Loading() {
  return (
    <div className="space-y-6 w-full animate-fade-in">
      
      {/* 1. SKELETON METRIC SUMMARIES */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Metric Card 1 Skeleton */}
        <div className="bg-white rounded-2xl border border-slate-200/60 p-5 shadow-sm">
          <div className="h-3 w-28 bg-slate-200 rounded animate-pulse mb-3" />
          <div className="h-8 w-24 bg-slate-100 rounded animate-pulse" />
        </div>
        {/* Metric Card 2 Skeleton */}
        <div className="bg-white rounded-2xl border border-slate-200/60 p-5 shadow-sm">
          <div className="h-3 w-32 bg-slate-200 rounded animate-pulse mb-3" />
          <div className="h-8 w-40 bg-slate-100 rounded animate-pulse" />
        </div>
      </div>

      {/* 2. SKELETON LEDGER TABLE */}
      <div className="bg-white rounded-2xl border border-slate-200/60 shadow-xl shadow-slate-100/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-left">
            <thead className="bg-slate-50/70 border-b border-slate-100">
              <tr>
                <th className="px-6 py-4"><div className="h-3 w-24 bg-slate-200 rounded animate-pulse" /></th>
                <th className="px-6 py-4"><div className="h-3 w-12 bg-slate-200 rounded animate-pulse" /></th>
                <th className="px-6 py-4"><div className="h-3 w-16 bg-slate-200 rounded animate-pulse" /></th>
                <th className="px-6 py-4"><div className="h-3 w-20 bg-slate-200 rounded animate-pulse" /></th>
                <th className="px-6 py-4"><div className="h-3 w-24 bg-slate-200 rounded animate-pulse" /></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {/* Render 4 mock animated skeleton table rows */}
              {[...Array(4)].map((_, index) => (
                <tr key={index} className="transition-colors duration-150">
                  <td className="px-6 py-5"><div className="h-4 w-44 bg-slate-100 rounded-lg animate-pulse" /></td>
                  <td className="px-6 py-5"><div className="h-5 w-10 bg-slate-100 rounded animate-pulse" /></td>
                  <td className="px-6 py-5"><div className="h-4 w-20 bg-slate-100 rounded animate-pulse" /></td>
                  <td className="px-6 py-5"><div className="h-4 w-28 bg-slate-100 font-mono rounded animate-pulse" /></td>
                  <td className="px-6 py-5"><div className="h-3 w-24 bg-slate-100 rounded animate-pulse" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}