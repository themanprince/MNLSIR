"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getAllProducts, getAllStores, getStockBalances, getStockTakes, submitStockTake } from "@/api";
import { STOCK_TAKE_COPY } from "@/CONSTANTS";
import FeedbackAlert from "@/components/FeedbackAlert";

// Keep the displayed names readable without changing the underlying values.
function formatStoreName(storeName) {
    if (!storeName) return "Unnamed store";
    return storeName.replace(/(^\w|\s+\w)/g, (match) => match.toUpperCase());
}

function formatProductName(productName) {
    if (!productName) return "Unnamed product";
    return productName.replace(/(^\w|\s+\w)/g, (match) => match.toUpperCase());
}

function getAvailableUnits(product) {
    if (!product) {
        return [];
    }

    const units = new Set([product.base_unit || product.default_unit || product.unit || "pcs"]);

    (product.unit_conversions || []).forEach((conversion) => {
        if (conversion?.unit) {
            units.add(conversion.unit);
        }
    });

    return Array.from(units);
}

export default function StockBalancesPage() {
    const [stores, setStores] = useState([]);
    const [products, setProducts] = useState([]);
    const [stockBalances, setStockBalances] = useState([]);
    const [stockTakes, setStockTakes] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [feedback, setFeedback] = useState("");
    const [storeId, setStoreId] = useState("");
    const [productId, setProductId] = useState("");
    const [unit, setUnit] = useState("");
    const [quantity, setQuantity] = useState("");
    const [stocktakeDate, setStocktakeDate] = useState(new Date().toISOString().slice(0, 10));
    const [remarks, setRemarks] = useState("");

    // Load the catalog and recent stock takes once so the form stays responsive.
    const loadCatalogData = useCallback(async () => {
        try {
            setIsLoading(true);
            setError("");
            const [storeResponse, productResponse, stockTakeResponse] = await Promise.all([
                getAllStores(),
                getAllProducts(),
                getStockTakes()
            ]);

            const normalizedStores = Array.isArray(storeResponse)
                ? storeResponse
                : Array.isArray(storeResponse?.stores)
                    ? storeResponse.stores
                    : [];
            const normalizedProducts = Array.isArray(productResponse)
                ? productResponse
                : Array.isArray(productResponse?.products)
                    ? productResponse.products
                    : [];
            const normalizedStockTakes = Array.isArray(stockTakeResponse)
                ? stockTakeResponse
                : Array.isArray(stockTakeResponse?.stock_takes)
                    ? stockTakeResponse.stock_takes
                    : [];

            setStores(normalizedStores);
            setProducts(normalizedProducts);
            setStockTakes(normalizedStockTakes);

            if (normalizedStores.length > 0 && !storeId) {
                setStoreId(String(normalizedStores[0].store_id ?? normalizedStores[0].id));
            }

            if (normalizedProducts.length > 0 && !productId) {
                setProductId(String(normalizedProducts[0].product_id ?? normalizedProducts[0].id));
            }
        } catch (loadError) {
            setError(loadError.message || "We could not load inventory data yet.");
        } finally {
            setIsLoading(false);
        }
    }, [productId, storeId]);

    const loadStoreBalances = useCallback(async (selectedStoreId) => {
        if (!selectedStoreId) {
            setStockBalances([]);
            return;
        }

        try {
            const balanceResponse = await getStockBalances(selectedStoreId);
            const normalizedBalances = Array.isArray(balanceResponse?.items)
                ? balanceResponse.items
                : [];
            setStockBalances(normalizedBalances);
        } catch (loadError) {
            setError(loadError.message || "We could not load stock balances yet.");
        }
    }, []);

    useEffect(() => {
        loadCatalogData();
    }, [loadCatalogData]);

    useEffect(() => {
        if (storeId) {
            loadStoreBalances(storeId);
        }
    }, [loadStoreBalances, storeId]);

    useEffect(() => {
        const selectedProduct = products.find((product) => String(product.product_id ?? product.id) === String(productId));
        const availableUnits = getAvailableUnits(selectedProduct);

        if (availableUnits.length === 0) {
            setUnit("");
            return;
        }

        setUnit((currentUnit) => {
            if (currentUnit && availableUnits.includes(currentUnit)) {
                return currentUnit;
            }

            return availableUnits[0];
        });
    }, [productId, products]);

    const currentBalanceSummary = useMemo(() => {
        if (!storeId || stockBalances.length === 0) {
            return "No current balance";
        }

        const selectedStoreBalance = stockBalances.find((item) => String(item.product_id) === String(productId));
        if (!selectedStoreBalance) {
            return "No current balance";
        }

        return `${selectedStoreBalance.available_quantity ?? 0} ${selectedStoreBalance.unit ?? "pcs"}`;
    }, [productId, stockBalances, storeId]);

    async function handleSubmit(event) {
        event.preventDefault();

        const trimmedQuantity = quantity.trim();

        if (!storeId || !productId) {
            setError("Please select both a store and a product.");
            setFeedback("");
            return;
        }

        if (!trimmedQuantity) {
            setError("Quantity is required.");
            setFeedback("");
            return;
        }

        const parsedQuantity = Number(trimmedQuantity);

        if (!Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
            setError("Quantity must be greater than zero.");
            setFeedback("");
            return;
        }

        if (!unit) {
            setError("Please select the unit used for this stock take.");
            setFeedback("");
            return;
        }

        try {
            setIsSubmitting(true);
            setError("");
            setFeedback("");
            await submitStockTake({
                storeId,
                productId,
                targetQuantity: parsedQuantity,
                stocktakeDate,
                remarks,
                recordedBy: 1,
                unit
            });
            setQuantity("");
            setRemarks("");
            setFeedback("Stock take saved successfully.");
            await loadCatalogData();
            await loadStoreBalances(storeId);
        } catch (submitError) {
            setError(submitError.message || "We could not save the stock take.");
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
                            Inventory control
                        </span>
                        <div className="space-y-2">
                            <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                                {STOCK_TAKE_COPY.heading}
                            </h1>
                            <p className="text-sm leading-7 text-slate-600">
                                {STOCK_TAKE_COPY.description}
                            </p>
                        </div>
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 shadow-sm">
                        <p className="font-semibold text-slate-900">{currentBalanceSummary}</p>
                        <p>{STOCK_TAKE_COPY.summaryLabel}</p>
                    </div>
                </div>
            </section>

            <section className="grid gap-8 xl:grid-cols-[1.05fr_0.95fr]">
                <div className="rounded-3xl border border-slate-200/70 bg-white p-8 shadow-sm">
                    <div className="mb-6">
                        <h2 className="text-xl font-semibold text-slate-900">{STOCK_TAKE_COPY.heading}</h2>
                        <p className="mt-1 text-sm text-slate-500">Choose a store and product, then record the count you observed.</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-6">
                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <label htmlFor="store-select" className="text-sm font-semibold text-slate-700">
                                    {STOCK_TAKE_COPY.storeLabel}
                                </label>
                                <select
                                    id="store-select"
                                    value={storeId}
                                    required
                                    onChange={(event) => setStoreId(event.target.value)}
                                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                                >
                                    <option value="">Select a store</option>
                                    {stores.map((store) => {
                                        const id = store.store_id ?? store.id;
                                        return (
                                            <option key={id} value={id}>
                                                {formatStoreName(store.store_name || store.name || "")}
                                            </option>
                                        );
                                    })}
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label htmlFor="product-select" className="text-sm font-semibold text-slate-700">
                                    {STOCK_TAKE_COPY.productLabel}
                                </label>
                                <select
                                    id="product-select"
                                    value={productId}
                                    required
                                    onChange={(event) => setProductId(event.target.value)}
                                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                                >
                                    <option value="">Select a product</option>
                                    {products.map((product) => {
                                        const id = product.product_id ?? product.id;
                                        return (
                                            <option key={id} value={id}>
                                                {formatProductName(product.product_name || product.name || "")}
                                            </option>
                                        );
                                    })}
                                </select>
                            </div>
                        </div>

                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <label htmlFor="quantity-input" className="text-sm font-semibold text-slate-700">
                                    {STOCK_TAKE_COPY.quantityLabel}
                                </label>
                                <input
                                    id="quantity-input"
                                    type="number"
                                    min="0.0001"
                                    step="0.0001"
                                    value={quantity}
                                    required
                                    onChange={(event) => setQuantity(event.target.value)}
                                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                                />
                            </div>

                            <div className="space-y-2">
                                <label htmlFor="unit-select" className="text-sm font-semibold text-slate-700">
                                    {STOCK_TAKE_COPY.unitLabel}
                                </label>
                                <select
                                    id="unit-select"
                                    value={unit}
                                    required
                                    onChange={(event) => setUnit(event.target.value)}
                                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                                >
                                    <option value="">Select a unit</option>
                                    {getAvailableUnits(products.find((product) => String(product.product_id ?? product.id) === String(productId))).map((availableUnit) => (
                                        <option key={availableUnit} value={availableUnit}>
                                            {availableUnit}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="stocktake-date" className="text-sm font-semibold text-slate-700">
                                {STOCK_TAKE_COPY.dateLabel}
                            </label>
                            <input
                                id="stocktake-date"
                                type="date"
                                value={stocktakeDate}
                                required
                                onChange={(event) => setStocktakeDate(event.target.value)}
                                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                            />
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="remarks-input" className="text-sm font-semibold text-slate-700">
                                {STOCK_TAKE_COPY.remarksLabel}
                            </label>
                            <textarea
                                id="remarks-input"
                                rows="3"
                                value={remarks}
                                onChange={(event) => setRemarks(event.target.value)}
                                placeholder={STOCK_TAKE_COPY.remarksPlaceholder}
                                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                            />
                        </div>

                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                            <p className="text-sm text-slate-500">This creates a baseline stock movement that can later feed the stock-balance experience.</p>
                            <button
                                type="submit"
                                disabled={isSubmitting || stores.length === 0 || products.length === 0}
                                className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                            >
                                {isSubmitting ? "Saving..." : STOCK_TAKE_COPY.submitLabel}
                            </button>
                        </div>

                        {error ? <FeedbackAlert kind="error" message={error} /> : null}
                        {feedback ? <FeedbackAlert kind="success" message={feedback} /> : null}
                    </form>
                </div>

                <div className="rounded-3xl border border-slate-200/70 bg-white p-8 shadow-sm">
                    <div className="mb-6">
                        <h2 className="text-xl font-semibold text-slate-900">Recent stock takes</h2>
                        <p className="mt-1 text-sm text-slate-500">A clear history of the baseline inventory values captured for your stores.</p>
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
                    ) : stockTakes.length === 0 ? (
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
                            <h3 className="text-base font-semibold text-slate-900">{STOCK_TAKE_COPY.emptyTitle}</h3>
                            <p className="mt-2 text-sm text-slate-500">{STOCK_TAKE_COPY.emptyMessage}</p>
                        </div>
                    ) : (
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
                    )}
                </div>
            </section>
        </div>
    );
}
