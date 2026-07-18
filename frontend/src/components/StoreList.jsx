"use client";

import EmptyState from "./EmptyState";
import LoadingSkeletonList from "./LoadingSkeletonList";

// Presentational list for stores. The page decides which data to pass in.
export default function StoreList({ stores, isLoading, error, emptyTitle, emptyMessage }) {
    if (isLoading) {
        return <LoadingSkeletonList count={4} />;
    }

    if (error && stores.length === 0) {
        return <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>;
    }

    if (stores.length === 0) {
        return <EmptyState title={emptyTitle} message={emptyMessage} />;
    }

    return (
        <div className="space-y-3">
            {stores.map((store, index) => {
                const storeName = store["store_name"];
                const storeId = store["store_id"];

                return (
                    <article
                        key={storeId}
                        className="group rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:border-blue-200 hover:bg-white hover:shadow-sm"
                    >
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
                                        {index + 1}
                                    </span>
                                    <div>
                                        <h3 className="text-base font-semibold text-slate-900">{storeName}</h3>
                                        <p className="text-sm text-slate-500">Store ID #{storeId}</p>
                                    </div>
                                </div>
                            </div>
                            <span className="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
                                Active
                            </span>
                        </div>
                    </article>
                );
            })}
        </div>
    );
}
