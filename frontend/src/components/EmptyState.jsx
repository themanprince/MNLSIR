"use client";

// Consistent empty state for lists that have no rows yet.
export default function EmptyState({ title, message, children }) {
    return (
        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
            {title ? <h3 className="text-base font-semibold text-slate-900">{title}</h3> : null}
            {message ? <p className="mt-2 text-sm text-slate-500">{message}</p> : null}
            {children}
        </div>
    );
}
