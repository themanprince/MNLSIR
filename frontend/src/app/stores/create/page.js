"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { createStore } from "@/api";
import { CREATE_STORE_COPY } from "@/CONSTANTS";
import PageHero from "@/components/PageHero";
import PageSection from "@/components/PageSection";
import SectionCard from "@/components/SectionCard";
import StoreCreationForm from "@/components/StoreCreationForm";
import StoreCreateInfoPanel from "@/components/StoreCreateInfoPanel";

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
            <PageHero
                badge="Inventory setup"
                title={CREATE_STORE_COPY.heading}
                description={CREATE_STORE_COPY.description}
                summaryValue={CREATE_STORE_COPY.helperText}
                summaryLabel=""
            />

            <section className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
                <SectionCard>
                    <StoreCreationForm
                        storeName={storeName}
                        onStoreNameChange={(event) => {
                            setStoreName(event.target.value);
                            if (error) setError("");
                        }}
                        isSubmitting={isSubmitting}
                        isReady={isReady}
                        onSubmit={handleSubmit}
                        error={error}
                        feedback={feedback}
                        helperText={CREATE_STORE_COPY.helperText}
                        submitLabel={CREATE_STORE_COPY.submitLabel}
                        inputLabel={CREATE_STORE_COPY.inputLabel}
                        inputPlaceholder={CREATE_STORE_COPY.inputPlaceholder}
                    />
                </SectionCard>

                <StoreCreateInfoPanel />
            </section>
        </div>
    );
}
