"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createProduct, getAllProducts } from "@/api";
import { useGetUnits } from "@/hooks";
import { PRODUCT_LIST_COPY, CREATE_PRODUCT_FORM_COPY } from "@/CONSTANTS";
import PageHero from "@/components/PageHero";
import PageSection from "@/components/PageSection";
import ProductCatalog from "@/components/ProductCatalog";
import ProductCreationForm from "@/components/ProductCreationForm";
import SectionCard from "@/components/SectionCard";

// Keep the product card labels readable without changing the stored values.
function formatProductName(productName) {
    if (!productName) return "Unnamed product";
    return productName.replace(/(^\w|\s+\w)/g, (match) => match.toUpperCase());
}

function createConversionRule() {
    return {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`, // Each new conversion row gets a unique id so React can manage it safely.
        unitID: -1,
        multiplierToBase: 0
    };
}

export default function ProductsPage() {
    const [units, setUnits, unitsLoading, unitsLoadingError] = useGetUnits();
    const [products, setProducts] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [feedback, setFeedback] = useState("");
    const [nameOfProductToCreate, setNameOfProductToCreate] = useState("");
    const [baseUnitIDOfProductToCreate, setBaseUnitIDOfProductToCreate] = useState(-1);
    const [conversionRulesOfProductToCreate, setConversionRulesOfProductToCreate] = useState([createConversionRule()]);

    if(unitsLoadingError) {
        throw new Error(`Error Loading Units --- ${unitsLoadingError}`);
    }

    const loadProducts = useCallback(async () => {
        // Keep the list of products in sync after create/update actions
        try {
            setIsLoading(true);
            setError("");
            setProducts(await getAllProducts());
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
        setConversionRulesOfProductToCreate((currentRules) => currentRules.map((rule) => (rule.id === ruleId ? { ...rule, [field]: value } : rule)));
    }

    function addConversionRule() {
        setConversionRulesOfProductToCreate((currentRules) => [...currentRules, createConversionRule()]);
    }

    function removeConversionRule(ruleId) {
        setConversionRulesOfProductToCreate((currentRules) => currentRules.filter((rule) => rule.id !== ruleId));
    }

    async function handleSubmit(event) {
        event.preventDefault();

        const trimmedName = nameOfProductToCreate.trim();

        if (!baseUnitIDOfProductToCreate) {
            setError("Please add a base unit for the product.");
            setFeedback("");
            return;
        }

        const normalizedConversions = conversionRulesOfProductToCreate
            .map((rule) => ({
                "unit_id": Number(rule.unitID),
                "multiplier_to_base": Number(rule.multiplierToBase)
            }));

        const emptyUnitOrMultiplierInConversion = normalizedConversions.find((rule) => (!rule["unit_id"]) || (!rule["multiplier_to_base"]));

        if (emptyUnitOrMultiplierInConversion) {
            setError("Each conversion needs a a value for unit and multiplier_to_base");
            setFeedback("");
            return;
        }
        
        const invalidConversion = normalizedConversions.find((rule) => !Number.isFinite(rule.multiplier_to_base) || rule.multiplier_to_base <= 0);

        if (invalidConversion) {
            setError("Each conversion needs a positive multiplier to the base unit.");
            setFeedback("");
            return;
        }

        const duplicateConversionUnits = normalizedConversions.some((rule, index) => normalizedConversions.findIndex((candidate) => candidate.unitID === rule.unitID) !== index);

        if (duplicateConversionUnits) {
            setError("Please avoid repeating the same conversion unit more than once.");
            setFeedback("");
            return;
        }

        try {
            setIsSubmitting(true);
            setError("");
            setFeedback("");
            await createProduct(trimmedName, baseUnitIDOfProductToCreate, normalizedConversions);
            setFeedback("Product created successfully.");
            setNameOfProductToCreate("");
            setBaseUnitIDOfProductToCreate(-1);
            setConversionRulesOfProductToCreate([createConversionRule()]);
            await loadProducts();
        } catch (submitError) {
            setError(submitError.message || "We could not create that product.");
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="space-y-8">
            <PageHero
                badge="Inventory catalog"
                title={PRODUCT_LIST_COPY.heading}
                description={PRODUCT_LIST_COPY.description}
                summaryValue={summaryLabel}
                summaryLabel={PRODUCT_LIST_COPY.countLabel}
            />

            <PageSection>
                <SectionCard title={CREATE_PRODUCT_FORM_COPY.title} description={CREATE_PRODUCT_FORM_COPY.description}>
                    <ProductCreationForm
                        productName={nameOfProductToCreate}
                        onProductNameChange={(event) => {
                            setNameOfProductToCreate(event.target.value);
                        }}
                        baseUnitID={baseUnitIDOfProductToCreate}
                        onBaseUnitIDChange={(event) => {
                            setBaseUnitIDOfProductToCreate(event.target.value);
                        }}
                        conversionRules={conversionRulesOfProductToCreate}
                        updateConversionRule={updateConversionRule}
                        addConversionRule={addConversionRule}
                        removeConversionRule={removeConversionRule}
                        allowedUnits={units}
                        isSubmitting={isSubmitting}
                        onSubmit={handleSubmit}
                        error={error}
                        feedback={feedback}
                        inputLabel={PRODUCT_LIST_COPY.inputLabel}
                        inputPlaceholder={PRODUCT_LIST_COPY.inputPlaceholder}
                        unitLabel={PRODUCT_LIST_COPY.unitLabel}
                        unitPlaceholder={PRODUCT_LIST_COPY.unitPlaceholder}
                        submitLabel={PRODUCT_LIST_COPY.submitLabel}
                        helperText={PRODUCT_LIST_COPY.helperText}
                        conversionLabel={PRODUCT_LIST_COPY.conversionLabel}
                        conversionDescription={PRODUCT_LIST_COPY.conversionDescription}
                        addConversionLabel={PRODUCT_LIST_COPY.addConversionLabel}
                        conversionUnitLabel={PRODUCT_LIST_COPY.conversionUnitLabel}
                        conversionAmountLabel={PRODUCT_LIST_COPY.conversionAmountLabel}
                        noConversionsText={PRODUCT_LIST_COPY.noConversionsText}
                    />
                </SectionCard>

                <SectionCard title={PRODUCT_LIST_COPY.heading} description={PRODUCT_LIST_COPY.description}>
                    <ProductCatalog
                        products={products}
                        isLoading={isLoading}
                        error={error}
                        emptyTitle={PRODUCT_LIST_COPY.emptyTitle}
                        emptyMessage={PRODUCT_LIST_COPY.emptyMessage}
                        formatProductName={formatProductName}
                    />
                </SectionCard>
            </PageSection>
        </div>
    );
}
