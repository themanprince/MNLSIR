"use client";

// Reusable loading skeleton for list-style panels across the inventory pages.
export default function LoadingSkeletonList({ count = 4 }) {
    return (
        <div className="space-y-3">
            {[...Array(count)].map((_, index) => (
                <div key={index} className="animate-pulse rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="h-4 w-32 rounded bg-slate-200" />
                    <div className="mt-2 h-3 w-48 rounded bg-slate-100" />
                </div>
            ))}
        </div>
    );
}
