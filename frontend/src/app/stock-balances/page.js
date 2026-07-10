"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getAllProducts, getAllStores, getStockBalances, getStockTakes, submitStockTake } from "@/api";
import { STOCK_TAKE_COPY } from "@/CONSTANTS";
import PageHero from "@/components/PageHero";
import PageSection from "@/components/PageSection";
import SectionCard from "@/components/SectionCard";
import StockTakeForm from "@/components/StockTakeForm";
import StockTakeHistory from "@/components/StockTakeHistory";

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

    const units = new Set([product.base_unit || product.default_unit || product.unit]);

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
            <PageHero
                badge="Inventory control"
                title={STOCK_TAKE_COPY.heading}
                description={STOCK_TAKE_COPY.description}
                summaryValue={currentBalanceSummary}
                summaryLabel={STOCK_TAKE_COPY.summaryLabel}
            />

            <PageSection>
                <SectionCard title={STOCK_TAKE_COPY.heading} description="Choose a store and product, then record the count you observed.">
                    <StockTakeForm
                        storeId={storeId}
                        onStoreChange={(event) => setStoreId(event.target.value)}
                        productId={productId}
                        onProductChange={(event) => setProductId(event.target.value)}
                        quantity={quantity}
                        onQuantityChange={(event) => setQuantity(event.target.value)}
                        unit={unit}
                        onUnitChange={(event) => setUnit(event.target.value)}
                        stocktakeDate={stocktakeDate}
                        onDateChange={(event) => setStocktakeDate(event.target.value)}
                        remarks={remarks}
                        onRemarksChange={(event) => setRemarks(event.target.value)}
                        stores={stores}
                        products={products}
                        availableUnits={getAvailableUnits(products.find((product) => String(product.product_id ?? product.id) === String(productId)))}
                        isSubmitting={isSubmitting}
                        onSubmit={handleSubmit}
                        error={error}
                        feedback={feedback}
                        submitLabel={STOCK_TAKE_COPY.submitLabel}
                        helperText="This creates a baseline stock movement that can later feed the stock-balance experience."
                        formatStoreName={formatStoreName}
                        formatProductName={formatProductName}
                    />
                </SectionCard>

                <SectionCard title="Recent stock takes" description="A clear history of the baseline inventory values captured for your stores.">
                    <StockTakeHistory
                        stockTakes={stockTakes}
                        stores={stores}
                        products={products}
                        isLoading={isLoading}
                        error={error}
                        emptyTitle={STOCK_TAKE_COPY.emptyTitle}
                        emptyMessage={STOCK_TAKE_COPY.emptyMessage}
                        formatStoreName={formatStoreName}
                        formatProductName={formatProductName}
                    />
                </SectionCard>
            </PageSection>
        </div>
    );
}
