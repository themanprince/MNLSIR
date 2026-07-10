"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createProduct, getAllProducts } from "@/api";
import { ALLOWED_PRODUCT_UNITS, PRODUCT_LIST_COPY } from "@/CONSTANTS";
import FeedbackAlert from "@/components/FeedbackAlert";
import ProductUnitConversionForm from "@/components/ProductUnitConversionForm";

// Keep the product card labels readable without changing the stored values.
function formatProductName(productName) {
    if (!productName) return "Unnamed product";
    return productName.replace(/(^\w|\s+\w)/g, (match) => match.toUpperCase());
}

// Each new conversion row gets a unique id so React can manage it safely.
function createConversionRule() {
    return {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        unit: "",
        multiplierToBase: ""
    };
}

export default function ProductsPage() {
    const [products, setProducts] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [feedback, setFeedback] = useState("");
    const [productName, setProductName] = useState("");
    const [baseUnit, setBaseUnit] = useState("");
    const [conversionRules, setConversionRules] = useState([createConversionRule()]);

    // Keep the list of products in sync after create/update actions.

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

    function updateConversionRule(ruleId, field, value) {
        setConversionRules((currentRules) => currentRules.map((rule) => (rule.id === ruleId ? { ...rule, [field]: value } : rule)));
    }

    function addConversionRule() {
        setConversionRules((currentRules) => [...currentRules, createConversionRule()]);
    }

    function removeConversionRule(ruleId) {
        setConversionRules((currentRules) => currentRules.filter((rule) => rule.id !== ruleId));
    }

    async function handleSubmit(event) {
        event.preventDefault();

        const trimmedName = productName.trim();
        const trimmedBaseUnit = baseUnit.trim();

        if (trimmedName.length < 2) {
            setError("Product names should be at least 2 characters long.");
            setFeedback("");
            return;
        }

        if (!trimmedBaseUnit) {
            setError("Please add a base unit for the product.");
            setFeedback("");
            return;
        }

        const normalizedConversions = conversionRules
            .filter((rule) => rule.unit && rule.multiplierToBase !== "")
            .map((rule) => ({
                unit: rule.unit.trim().toLowerCase(),
                multiplier_to_base: Number(rule.multiplierToBase)
            }));

        const invalidConversion = normalizedConversions.find((rule) => !Number.isFinite(rule.multiplier_to_base) || rule.multiplier_to_base <= 0);

        if (invalidConversion) {
            setError("Each conversion needs a positive multiplier to the base unit.");
            setFeedback("");
            return;
        }

        const duplicateConversionUnits = normalizedConversions.some((rule, index) => normalizedConversions.findIndex((candidate) => candidate.unit === rule.unit) !== index);

        if (duplicateConversionUnits) {
            setError("Please avoid repeating the same conversion unit more than once.");
            setFeedback("");
            return;
        }

        try {
            setIsSubmitting(true);
            setError("");
            setFeedback("");
            await createProduct(trimmedName, trimmedBaseUnit, {
                baseUnit: trimmedBaseUnit,
                conversions: normalizedConversions
            });
            setProductName("");
            setBaseUnit("");
            setConversionRules([createConversionRule()]);
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
                                required
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
                                value={baseUnit}
                                required
                                onChange={(event) => {
                                    setBaseUnit(event.target.value);
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

                        <ProductUnitConversionForm
                            baseUnit={baseUnit}
                            setBaseUnit={setBaseUnit}
                            conversionRules={conversionRules}
                            updateConversionRule={updateConversionRule}
                            addConversionRule={addConversionRule}
                            removeConversionRule={removeConversionRule}
                            allowedUnits={ALLOWED_PRODUCT_UNITS}
                            unitLabel={PRODUCT_LIST_COPY.unitLabel}
                            unitPlaceholder={PRODUCT_LIST_COPY.unitPlaceholder}
                            conversionLabel={PRODUCT_LIST_COPY.conversionLabel}
                            conversionDescription={PRODUCT_LIST_COPY.conversionDescription}
                            addConversionLabel={PRODUCT_LIST_COPY.addConversionLabel}
                            conversionUnitLabel={PRODUCT_LIST_COPY.conversionUnitLabel}
                            conversionAmountLabel={PRODUCT_LIST_COPY.conversionAmountLabel}
                            noConversionsText={PRODUCT_LIST_COPY.noConversionsText}
                            helperText="The base unit and conversion rules are stored with the product so later stock operations can stay consistent."
                        />

                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                            <p className="text-sm text-slate-500">The base unit and conversion rules are stored with the product so later stock operations can stay consistent.</p>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                            >
                                {isSubmitting ? "Creating..." : PRODUCT_LIST_COPY.submitLabel}
                            </button>
                        </div>

                        {error ? <FeedbackAlert kind="error" message={error} /> : null}
                        {feedback ? <FeedbackAlert kind="success" message={feedback} /> : null}
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
                    )}
                </div>
            </section>
        </div>
    );
}
