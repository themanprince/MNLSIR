"use client";

import FeedbackAlert from "./FeedbackAlert";

// Form shell for recording a stock take while keeping presentation logic reusable.
export default function StockTakeForm({
    storeId,
    onStoreChange,
    productId,
    onProductChange,
    quantity,
    onQuantityChange,
    unit,
    onUnitChange,
    stocktakeDate,
    onDateChange,
    remarks,
    onRemarksChange,
    stores,
    products,
    availableUnits,
    isSubmitting,
    onSubmit,
    error,
    feedback,
    submitLabel,
    helperText,
    formatStoreName,
    formatProductName
}) {
    return (
        <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-6">
            <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                    <label htmlFor="store-select" className="text-sm font-semibold text-slate-700">
                        Store
                    </label>
                    <select id="store-select" value={storeId} required onChange={onStoreChange} className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100">
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
                        Product
                    </label>
                    <select id="product-select" value={productId} required onChange={onProductChange} className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100">
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
                        Quantity
                    </label>
                    <input id="quantity-input" type="number" min="0.0001" step="0.0001" value={quantity} required onChange={onQuantityChange} className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
                </div>

                <div className="space-y-2">
                    <label htmlFor="unit-select" className="text-sm font-semibold text-slate-700">
                        Unit
                    </label>
                    <select id="unit-select" value={unit} required onChange={onUnitChange} className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100">
                        <option value="">Select a unit</option>
                        {availableUnits.map((availableUnit) => (
                            <option key={availableUnit} value={availableUnit}>
                                {availableUnit}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="space-y-2">
                <label htmlFor="stocktake-date" className="text-sm font-semibold text-slate-700">
                    Date
                </label>
                <input id="stocktake-date" type="date" value={stocktakeDate} required onChange={onDateChange} className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
            </div>

            <div className="space-y-2">
                <label htmlFor="remarks-input" className="text-sm font-semibold text-slate-700">
                    Remarks
                </label>
                <textarea id="remarks-input" rows="3" value={remarks} onChange={onRemarksChange} placeholder="Optional notes" className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-slate-500">{helperText}</p>
                <button type="submit" disabled={isSubmitting} className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300">
                    {isSubmitting ? "Saving..." : submitLabel}
                </button>
            </div>

            {error ? <FeedbackAlert kind="error" message={error} /> : null}
            {feedback ? <FeedbackAlert kind="success" message={feedback} /> : null}
        </form>
    );
}
