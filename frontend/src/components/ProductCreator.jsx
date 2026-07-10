"use client";

import { useMemo, useState } from "react";
import { createProduct } from "@/api";
import { ALLOWED_PRODUCT_UNITS, PRODUCT_LIST_COPY } from "@/CONSTANTS";
import ProductCreationForm from "./ProductCreationForm";

function createConversionRule() {
    return {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        unit: "",
        multiplierToBase: ""
    };
}

export default function ProductCreator({ onCreated }) {
    const [productName, setProductName] = useState("");
    const [baseUnit, setBaseUnit] = useState("");
    const [conversionRules, setConversionRules] = useState([createConversionRule()]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [feedback, setFeedback] = useState("");

    const helperText = useMemo(
        () => "The base unit and conversion rules are stored with the product so later stock operations can stay consistent.",
        []
    );

    const conversionsPayload = useMemo(() => {
        return conversionRules
            .filter((rule) => rule.unit && rule.multiplierToBase !== "")
            .map((rule) => ({
                unit: rule.unit.trim().toLowerCase(),
                multiplier_to_base: Number(rule.multiplierToBase)
            }));
    }, [conversionRules]);

    function updateConversionRule(ruleId, field, value) {
        setConversionRules((currentRules) =>
            currentRules.map((rule) => (rule.id === ruleId ? { ...rule, [field]: value } : rule))
        );
    }

    function addConversionRule() {
        setConversionRules((currentRules) => [...currentRules, createConversionRule()]);
    }

    function removeConversionRule(ruleId) {
        setConversionRules((currentRules) => currentRules.filter((rule) => rule.id !== ruleId));
    }

    function resetForm() {
        setProductName("");
        setBaseUnit("");
        setConversionRules([createConversionRule()]);
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

        const invalidConversion = conversionsPayload.find(
            (rule) => !Number.isFinite(rule.multiplier_to_base) || rule.multiplier_to_base <= 0
        );

        if (invalidConversion) {
            setError("Each conversion needs a positive multiplier to the base unit.");
            setFeedback("");
            return;
        }

        const duplicateConversionUnits = conversionsPayload.some(
            (rule, index) => conversionsPayload.findIndex((candidate) => candidate.unit === rule.unit) !== index
        );

        if (duplicateConversionUnits) {
            setError("Please avoid repeating the same conversion unit more than once.");
            setFeedback("");
            return;
        }

        try {
            setIsSubmitting(true);
            setError("");
            setFeedback("");

            await createProduct(trimmedName, {
                baseUnit: trimmedBaseUnit,
                conversions: conversionsPayload
            });

            resetForm();
            setFeedback("Product created successfully.");
            onCreated?.();
        } catch (submitError) {
            setError(submitError.message || "We could not create that product.");
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <ProductCreationForm
            productName={productName}
            onProductNameChange={(event) => {
                setProductName(event.target.value);
                if (error) setError("");
            }}
            baseUnit={baseUnit}
            onBaseUnitChange={(event) => {
                setBaseUnit(event.target.value);
                if (error) setError("");
            }}
            conversionRules={conversionRules}
            updateConversionRule={updateConversionRule}
            addConversionRule={addConversionRule}
            removeConversionRule={removeConversionRule}
            allowedUnits={ALLOWED_PRODUCT_UNITS}
            isSubmitting={isSubmitting}
            onSubmit={handleSubmit}
            error={error}
            feedback={feedback}
            inputLabel={PRODUCT_LIST_COPY.inputLabel}
            inputPlaceholder={PRODUCT_LIST_COPY.inputPlaceholder}
            unitLabel={PRODUCT_LIST_COPY.unitLabel}
            unitPlaceholder={PRODUCT_LIST_COPY.unitPlaceholder}
            submitLabel={PRODUCT_LIST_COPY.submitLabel}
            helperText={helperText}
            conversionLabel={PRODUCT_LIST_COPY.conversionLabel}
            conversionDescription={PRODUCT_LIST_COPY.conversionDescription}
            addConversionLabel={PRODUCT_LIST_COPY.addConversionLabel}
            conversionUnitLabel={PRODUCT_LIST_COPY.conversionUnitLabel}
            conversionAmountLabel={PRODUCT_LIST_COPY.conversionAmountLabel}
            noConversionsText={PRODUCT_LIST_COPY.noConversionsText}
        />
    );
}
