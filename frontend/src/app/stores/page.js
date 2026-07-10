"use client";

import { useEffect, useMemo, useState } from "react";
import { getAllStores } from "@/api";
import { CREATE_STORE_COPY, STORE_LIST_COPY } from "@/CONSTANTS";

function formatStoreName(storeName) {
    if (!storeName) return "Unnamed store";
    return storeName.replace(/(^\w|\s+\w)/g, (match) => match.toUpperCase());
}

export default function StoresPage() {
    const [stores, setStores] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let isMounted = true;

        async function loadStores() {
            try {
                setIsLoading(true);
                setError("");
                const response = await getAllStores();

                if (!isMounted) return;

                const normalizedStores = Array.isArray(response)
                    ? response
                    : Array.isArray(response?.stores)
                        ? response.stores
                        : [];

                setStores(normalizedStores);
            } catch (loadError) {
                if (!isMounted) return;
                setError(loadError.message || "We could not load the stores right now.");
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        }

        loadStores();

        return () => {
            isMounted = false;
        };
    }, []);

    const summaryLabel = useMemo(() => {
        if (stores.length === 0) return "0";
        return stores.length.toString();
    }, [stores]);

    return (
        <div className="space-y-8">
            <section className="rounded-3xl border border-slate-200/70 bg-white/90 p-8 shadow-[0_25px_80px_-30px_rgba(15,23,42,0.25)] backdrop-blur">
                <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                    <div className="max-w-2xl space-y-3">
                        <span className="inline-flex w-fit items-center rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-blue-600">
                            Store management
                        </span>
                        <div className="space-y-2">
                            <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                                {STORE_LIST_COPY.heading}
                            </h1>
                            <p className="text-sm leading-7 text-slate-600">
                                {STORE_LIST_COPY.description}
                            </p>
                        </div>
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 shadow-sm">
                        <p className="font-semibold text-slate-900">{summaryLabel}</p>
                        <p>{STORE_LIST_COPY.countLabel}</p>
                    </div>
                </div>
            </section>

            <section className="grid gap-8 xl:grid-cols-[1.05fr_0.95fr]">
                <div className="rounded-3xl border border-slate-200/70 bg-white p-8 shadow-sm">
                    <div className="mb-6 flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-semibold text-slate-900">{CREATE_STORE_COPY.heading}</h2>
                            <p className="mt-1 text-sm text-slate-500">{CREATE_STORE_COPY.description}</p>
                        </div>
                        <a
                            href="/stores"
                            className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                        >
                            Refresh list
                        </a>
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
                        <form className="flex flex-col gap-3 md:flex-row" action="/stores" method="get">
                            <div className="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">
                                {CREATE_STORE_COPY.helperText}
                            </div>
                            <button
                                type="button"
                                onClick={() => window.location.reload()}
                                className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
                            >
                                Reload stores
                            </button>
                        </form>
                    </div>
                </div>

                <div className="rounded-3xl border border-slate-200/70 bg-white p-8 shadow-sm">
                    <div className="mb-6 flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-semibold text-slate-900">{STORE_LIST_COPY.heading}</h2>
                            <p className="mt-1 text-sm text-slate-500">{STORE_LIST_COPY.description}</p>
                        </div>
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
                    ) : error ? (
                        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                            {error}
                        </div>
                    ) : stores.length === 0 ? (
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
                            <h3 className="text-base font-semibold text-slate-900">{STORE_LIST_COPY.emptyTitle}</h3>
                            <p className="mt-2 text-sm text-slate-500">{STORE_LIST_COPY.emptyMessage}</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {stores.map((store, index) => {
                                const storeName = formatStoreName(store.store_name || store.name || "");
                                const storeId = store.store_id ?? store.id ?? index + 1;

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
                    )}
                </div>
            </section>
        </div>
    );
}
