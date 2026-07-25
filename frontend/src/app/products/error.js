"use client";

import { PRODUCT_PAGE_ERROR_COPY } from "@/CONSTANTS";
import React, { useEffect } from "react";

export default function Error({ error, reset }) {
  useEffect(() => {
    console.error("Prince, an Exception occured:", error);
  }, [error]);

  return (
    <div className="max-w-xl mx-auto my-12 animate-fade-in">
      <div className="bg-white rounded-2xl border border-rose-100 shadow-2xl p-6 md:p-8 text-center space-y-5">
        
        {/* Modern Warn Icon Context Block */}
        <div className="h-14 w-14 rounded-2xl bg-rose-50 border border-rose-100 text-rose-500 flex items-center justify-center mx-auto text-xl shadow-inner font-bold">
          ⚠️
        </div>

        <div className="space-y-1.5">
          <h3 className="text-base font-black tracking-tight text-slate-900">
            {PRODUCT_PAGE_ERROR_COPY.heading}
          </h3>
          <p className="text-xs font-medium text-slate-500 max-w-sm mx-auto leading-relaxed">
            {PRODUCT_PAGE_ERROR_COPY.customMessage}
          </p>
        </div>

        {/* Technical debugging diagnostics block for developers */}
        <div className="bg-slate-50 border border-slate-200/60 rounded-xl p-3 text-left">
          <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 block mb-0.5">Exception</span>
          <code className="text-xs font-mono text-rose-600 block break-words">
            {error?.message || PRODUCT_PAGE_ERROR_COPY.customMessage}
          </code>
        </div>

        {/* Dynamic Context Control Interaction Trigger */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-2 pt-2">
          <button
            onClick={() => window.location.reload()}
            className="w-full sm:w-auto px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition"
          >
            Hard Reload App
          </button>
          
          <button
            onClick={() => reset()}
            className="w-full sm:w-auto px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold text-xs rounded-xl shadow-md shadow-blue-600/10 transition-all active:scale-[0.99]"
          >
            Re-Attempt Connection
          </button>
        </div>

      </div>
    </div>
  );
}