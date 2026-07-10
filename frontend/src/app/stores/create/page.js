"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { createStore, getAllStores } from "@/api";
import { CREATE_STORE_COPY } from "@/CONSTANTS";

export default function CreateStorePage() {
    const router = useRouter();
    const [storeName, setStoreName] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [feedback, setFeedback] = useState("");

    const isReady = useMemo(() => storeName.trim().length >= 3, [storeName]);

    async function handleSubmit(event) {
        event.preventDefault();

        if (!isReady) {
            setError("Store names should be at least 3 characters long.");
            setFeedback("");
            return;
        }

        setIsSubmitting(true);
        setError("");
        setFeedback("");

        try {
            await createStore(storeName.trim());
            await getAllStores();
            setFeedback(CREATE_STORE_COPY.successTitle);
            setStoreName("");
            router.refresh();
        } catch (submitError) {
            setError(submitError.message || CREATE_STORE_COPY.errorFallback);
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="space-y-8">
            <section className="rounded-3xl border border-slate-200/70 bg-white/90 p-8 shadow-[0_25px_80px_-30px_rgba(15,23,42,0.25)] backdrop-blur">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                    <div className="max-w-2xl space-y-3">
                        <span className="inline-flex w-fit items-center rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-blue-600">
                            Inventory setup
                        </span>
                        <div className="space-y-2">
                            <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                                {CREATE_STORE_COPY.heading}
                            </h1>
                            <p className="text-sm leading-7 text-slate-600">
                                {CREATE_STORE_COPY.description}
                            </p>
                        </div>
                    </div>

                    <div className="rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 shadow-sm">
                        <p className="font-semibold">{CREATE_STORE_COPY.helperText}</p>
                    </div>
                </div>
            </section>

            <section className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
                <form onSubmit={handleSubmit} className="rounded-3xl border border-slate-200/70 bg-white p-8 shadow-sm">
                    <div className="space-y-2">
                        <label htmlFor="store-name" className="text-sm font-semibold text-slate-700">
                            {CREATE_STORE_COPY.inputLabel}
                        </label>
                        <input
                            id="store-name"
                            name="store_name"
                            type="text"
                            value={storeName}
                            onChange={(event) => {
                                setStoreName(event.target.value);
                                if (error) setError("");
                            }}
                            placeholder={CREATE_STORE_COPY.inputPlaceholder}
                            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100"
                        />
                    </div>

                    <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <p className="text-sm text-slate-500">{CREATE_STORE_COPY.helperText}</p>
                        <button
                            type="submit"
                            disabled={isSubmitting || !isReady}
                            className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                        >
                            {isSubmitting ? "Creating..." : CREATE_STORE_COPY.submitLabel}
                        </button>
                    </div>

                    {error ? (
                        <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                            {error}
                        </div>
                    ) : null}

                    {feedback ? (
                        <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                            {CREATE_STORE_COPY.successMessage}
                        </div>
                    ) : null}
                </form>

                <aside className="rounded-3xl border border-slate-200/70 bg-slate-950 p-8 text-white shadow-[0_30px_80px_-35px_rgba(2,6,23,0.9)]">
                    <div className="space-y-4">
                        <div className="inline-flex rounded-full border border-white/10 bg-white/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-300">
                            What happens next
                        </div>
                        <h2 className="text-xl font-semibold">From here, you can immediately use the store in inventory workflows.</h2>
                        <ul className="space-y-3 text-sm leading-7 text-slate-300">
                            <li className="flex gap-3"><span className="mt-2 h-2.5 w-2.5 rounded-full bg-blue-400" />Track stock receipts and issues in one place.</li>
                            <li className="flex gap-3"><span className="mt-2 h-2.5 w-2.5 rounded-full bg-blue-400" />Review balances and stock take reports with less effort.</li>
                            <li className="flex gap-3"><span className="mt-2 h-2.5 w-2.5 rounded-full bg-blue-400" />Keep store records organized as your operations grow.</li>
                        </ul>
                    </div>
                </aside>
            </section>
        </div>
    );
}
