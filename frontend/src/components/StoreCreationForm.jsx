"use client";

import FeedbackAlert from "./FeedbackAlert";

// A focused form for creating a store without exposing its presentation details in the page.
export default function StoreCreationForm({
    storeName,
    onStoreNameChange,
    isSubmitting,
    isReady,
    onSubmit,
    error,
    feedback,
    helperText,
    submitLabel,
    inputLabel,
    inputPlaceholder
}) {
    return (
        <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-6">
            <div className="space-y-2">
                <label htmlFor="store-name" className="text-sm font-semibold text-slate-700">
                    {inputLabel}
                </label>
                <input
                    id="store-name"
                    type="text"
                    value={storeName}
                    onChange={onStoreNameChange}
                    placeholder={inputPlaceholder}
                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-slate-500">{helperText}</p>
                <button
                    type="submit"
                    disabled={isSubmitting || !isReady}
                    className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                    {isSubmitting ? "Creating..." : submitLabel}
                </button>
            </div>

            {error ? <FeedbackAlert kind="error" message={error} /> : null}
            {feedback ? <FeedbackAlert kind="success" message={feedback} /> : null}
        </form>
    );
}
