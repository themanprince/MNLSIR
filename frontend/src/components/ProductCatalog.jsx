"use client";

import EmptyState from "./EmptyState";
import LoadingSkeletonList from "./LoadingSkeletonList";

// Presentational list for products and their conversion rules.
export default function ProductCatalog({ products, isLoading, error, emptyTitle, emptyMessage, formatProductName }) {
    if (isLoading) {
        return <LoadingSkeletonList count={4} />;
    }

    if (error && products.length === 0) {
        return <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>;
    }

    if (products.length === 0) {
        return <EmptyState title={emptyTitle} message={emptyMessage} />;
    }

    return (
        <div className="space-y-3">
            {products.map((product, index) => {
                const productName = formatProductName(product.product_name || product.name || "");
                const productId = product.product_id ?? product.id ?? index + 1;
                const baseUnit = product.base_unit || product.default_unit || product.unit || "pcs";
                const conversions = Array.isArray(product.unit_conversions) ? product.unit_conversions : [];

                return (
                    <article
                        key={productId}
                        className="rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:border-blue-200 hover:bg-white hover:shadow-sm"
                    >
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex items-center gap-2">
                                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
                                    {index + 1}
                                </span>
                                <div>
                                    <h3 className="text-base font-semibold text-slate-900">{productName}</h3>
                                    <p className="text-sm text-slate-500">Product ID #{productId}</p>
                                </div>
                            </div>
                            <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-600">
                                {baseUnit}
                            </span>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                            {conversions.length > 0 ? conversions.map((conversion, conversionIndex) => (
                                <span key={`${productId}-${conversionIndex}`} className="rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
                                    1 {conversion.unit} = {conversion.multiplier_to_base ?? conversion.multiplierToBase} {baseUnit}
                                </span>
                            )) : (
                                <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-500">
                                    No conversions configured yet
                                </span>
                            )}
                        </div>
                    </article>
                );
            })}
        </div>
    );
}
