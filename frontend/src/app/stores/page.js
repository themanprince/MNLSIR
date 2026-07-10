"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createStore, getAllStores } from "@/api";
import { CREATE_STORE_COPY, STORE_LIST_COPY } from "@/CONSTANTS";
import PageHero from "@/components/PageHero";
import PageSection from "@/components/PageSection";
import SectionCard from "@/components/SectionCard";
import StoreCreationForm from "@/components/StoreCreationForm";
import StoreList from "@/components/StoreList";

function formatStoreName(storeName) {
    if (!storeName) return "Unnamed store";
    return storeName.replace(/(^\w|\s+\w)/g, (match) => match.toUpperCase());
}

export default function StoresPage() {
    const [stores, setStores] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [feedback, setFeedback] = useState("");
    const [storeName, setStoreName] = useState("");

    const loadStores = useCallback(async () => {
        try {
            setIsLoading(true);
            setError("");
            const response = await getAllStores();
            const normalizedStores = Array.isArray(response)
                ? response
                : Array.isArray(response?.stores)
                    ? response.stores
                    : [];

            setStores(normalizedStores);
        } catch (loadError) {
            setError(loadError.message || "We could not load the stores right now.");
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadStores();
    }, [loadStores]);

    const summaryLabel = useMemo(() => {
        if (stores.length === 0) return "0";
        return stores.length.toString();
    }, [stores]);

    async function handleSubmit(event) {
        event.preventDefault();

        const trimmedName = storeName.trim();

        if (trimmedName.length < 3) {
            setError("Store names should be at least 3 characters long.");
            setFeedback("");
            return;
        }

        try {
            setIsSubmitting(true);
            setError("");
            setFeedback("");
            await createStore(trimmedName);
            setStoreName("");
            setFeedback(CREATE_STORE_COPY.successTitle);
            await loadStores();
        } catch (submitError) {
            setError(submitError.message || CREATE_STORE_COPY.errorFallback);
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="space-y-8">
            <PageHero
                badge="Store management"
                title={STORE_LIST_COPY.heading}
                description={STORE_LIST_COPY.description}
                summaryValue={summaryLabel}
                summaryLabel={STORE_LIST_COPY.countLabel}
            />

            <PageSection>
                <SectionCard title={CREATE_STORE_COPY.heading} description={CREATE_STORE_COPY.description}>
                    <StoreCreationForm
                        storeName={storeName}
                        onStoreNameChange={(event) => {
                            setStoreName(event.target.value);
                            if (error) setError("");
                        }}
                        isSubmitting={isSubmitting}
                        onSubmit={handleSubmit}
                        error={error}
                        feedback={feedback}
                        helperText={CREATE_STORE_COPY.helperText}
                        submitLabel={CREATE_STORE_COPY.submitLabel}
                        inputLabel={CREATE_STORE_COPY.inputLabel}
                        inputPlaceholder={CREATE_STORE_COPY.inputPlaceholder}
                    />
                </SectionCard>

                <SectionCard title={STORE_LIST_COPY.heading} description={STORE_LIST_COPY.description}>
                    <StoreList
                        stores={stores}
                        isLoading={isLoading}
                        error={error}
                        emptyTitle={STORE_LIST_COPY.emptyTitle}
                        emptyMessage={STORE_LIST_COPY.emptyMessage}
                        formatStoreName={formatStoreName}
                    />
                </SectionCard>
            </PageSection>
        </div>
    );
}
