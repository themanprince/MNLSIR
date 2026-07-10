"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createProduct, getAllProducts } from "@/api";
import { ALLOWED_PRODUCT_UNITS, PRODUCT_LIST_COPY } from "@/CONSTANTS";

function formatProductName(productName) {
    if (!productName) return "Unnamed product";
    return productName.replace(/(^\w|\s+\w)/g, (match) => match.toUpperCase());
}

export default function ProductsPage() {
    const [products, setProducts] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [feedback, setFeedback] = useState("");
    const [productName, setProductName] = useState("");
    const [unit, setUnit] = useState("");

    const loadProducts = useCallback(async () => {
        try {
            setIsLoading(true);
            setError("");
            const response = await getAllProducts();
            const normalizedProducts = Array.isArray(response)
                ? response
                : Array.isArray(response?.products)
                    ? response.products
                    : [];

            setProducts(normalizedProducts);
        } catch (loadError) {
            setError(loadError.message || "We could not load the products right now.");
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadProducts();
    }, [loadProducts]);

    const summaryLabel = useMemo(() => {
        if (products.length === 0) return "0";
        return products.length.toString();
    }, [products]);

    async function handleSubmit(event) {
        event.preventDefault();

        const trimmedName = productName.trim();
        const trimmedUnit = unit.trim();

        if (trimmedName.length < 2) {
            setError("Product names should be at least 2 characters long.");
            setFeedback("");
            return;
        }

        if (!trimmedUnit) {
            setError("Please add a default unit for the product.");
            setFeedback("");
            return;
        }

        try {
            setIsSubmitting(true);
            setError("");
            setFeedback("");
            await createProduct(trimmedName, trimmedUnit);
            setProductName("");
            setUnit("");
            setFeedback("Product created successfully.");
            await loadProducts();
        } catch (submitError) {
            setError(submitError.message || "We could not create that product.");
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="space-y-8">
            <section className="rounded-3xl border border-slate-200/70 bg-white/90 p-8 shadow-[0_25px_80px_-30px_rgba(15,23,42,0.25)] backdrop-blur">
                <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                    <div className="max-w-2xl space-y-3">
                        <span className="inline-flex w-fit items-center rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-blue-600">
                            Inventory catalog
                        </span>
                        <div className="space-y-2">
                            <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                                {PRODUCT_LIST_COPY.heading}
                            </h1>
                            <p className="text-sm leading-7 text-slate-600">
                                {PRODUCT_LIST_COPY.description}
                            </p>
                        </div>
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 shadow-sm">
                        <p className="font-semibold text-slate-900">{summaryLabel}</p>
                        <p>{PRODUCT_LIST_COPY.countLabel}</p>
                    </div>
                </div>
            </section>

            <section className="grid gap-8 xl:grid-cols-[1.05fr_0.95fr]">
                <div className="rounded-3xl border border-slate-200/70 bg-white p-8 shadow-sm">
                    <div className="mb-6">
                        <h2 className="text-xl font-semibold text-slate-900">Create a product</h2>
                        <p className="mt-1 text-sm text-slate-500">Add a product so it can be used across receipts, issues, and balance views.</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-6">
                        <div className="space-y-2">
                            <label htmlFor="product-name" className="text-sm font-semibold text-slate-700">
                                {PRODUCT_LIST_COPY.inputLabel}
                            </label>
                            <input
                                id="product-name"
                                type="text"
                                value={productName}
                                onChange={(event) => {
                                    setProductName(event.target.value);
                                    if (error) setError("");
                                }}
                                placeholder={PRODUCT_LIST_COPY.inputPlaceholder}
                                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                            />
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="product-unit" className="text-sm font-semibold text-slate-700">
                                {PRODUCT_LIST_COPY.unitLabel}
                            </label>
                            <select
                                id="product-unit"
                                value={unit}
                                onChange={(event) => {
                                    setUnit(event.target.value);
                                    if (error) setError("");
                                }}
                                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                            >
                                <option value="">{PRODUCT_LIST_COPY.unitPlaceholder}</option>
                                {ALLOWED_PRODUCT_UNITS.map((allowedUnit) => (
                                    <option key={allowedUnit} value={allowedUnit}>
                                        {allowedUnit}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                            <p className="text-sm text-slate-500">Units are stored alongside each product to support later stock operations.</p>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                            >
                                {isSubmitting ? "Creating..." : PRODUCT_LIST_COPY.submitLabel}
                            </button>
                        </div>

                        {error ? (
                            <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                                {error}
                            </div>
                        ) : null}

                        {feedback ? (
                            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                                {feedback}
                            </div>
                        ) : null}
                    </form>
                </div>

                <div className="rounded-3xl border border-slate-200/70 bg-white p-8 shadow-sm">
                    <div className="mb-6">
                        <h2 className="text-xl font-semibold text-slate-900">{PRODUCT_LIST_COPY.heading}</h2>
                        <p className="mt-1 text-sm text-slate-500">{PRODUCT_LIST_COPY.description}</p>
                    </div>

                    {isLoading ? (
                        <div className="space-y-3">
                            {[...Array(4)].map((_, index) => (
                                <div key={index} className="animate-pulse rounded-2xl border border-slate-200 bg-slate-50 p-4">
                                    <div className="h-4 w-32 rounded bg-slate-200" />
                                    <div className="mt-2 h-3 w-48 rounded bg-slate-100" />
                                </div>
                            ))}
                        </div>
                    ) : error && products.length === 0 ? (
                        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                            {error}
                        </div>
                    ) : products.length === 0 ? (
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
                            <h3 className="text-base font-semibold text-slate-900">{PRODUCT_LIST_COPY.emptyTitle}</h3>
                            <p className="mt-2 text-sm text-slate-500">{PRODUCT_LIST_COPY.emptyMessage}</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {products.map((product, index) => {
                                const productName = formatProductName(product.product_name || product.name || "");
                                const productId = product.product_id ?? product.id ?? index + 1;
                                const unit = product.default_unit || product.unit || "pcs";

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
                                                {unit}
                                            </span>
                                        </div>
                                    </article>
                                );
                            })}
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
}
