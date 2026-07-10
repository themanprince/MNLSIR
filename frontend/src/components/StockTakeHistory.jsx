"use client";

import EmptyState from "./EmptyState";
import LoadingSkeletonList from "./LoadingSkeletonList";

// Presentational history for stock takes. The page provides the data and formatting helpers.
export default function StockTakeHistory({ stockTakes, stores, products, isLoading, error, emptyTitle, emptyMessage, formatStoreName, formatProductName }) {
    if (isLoading) {
        return <LoadingSkeletonList count={4} />;
    }

    if (error && stockTakes.length === 0) {
        return <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>;
    }

    if (stockTakes.length === 0) {
        return <EmptyState title={emptyTitle} message={emptyMessage} />;
    }

    return (
        <div className="space-y-3">
            {stockTakes.map((stockTake) => {
                const store = stores.find((item) => String(item.store_id ?? item.id) === String(stockTake.store_id));
                const product = products.find((item) => String(item.product_id ?? item.id) === String(stockTake.product_id));

                return (
                    <article key={stockTake.stocktake_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:border-blue-200 hover:bg-white hover:shadow-sm">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <h3 className="text-base font-semibold text-slate-900">
                                    {formatProductName(product?.product_name || product?.name || "")}
                                </h3>
                                <p className="mt-1 text-sm text-slate-500">
                                    {formatStoreName(store?.store_name || store?.name || "")} • {stockTake.stocktake_date}
                                </p>
                            </div>
                            <span className="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
                                {stockTake.target_quantity}
                            </span>
                        </div>
                    </article>
                );
            })}
        </div>
    );
}
