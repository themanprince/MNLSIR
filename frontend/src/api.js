import { BACKEND_URL } from "@/CONSTANTS";
import { getSKU } from "./helpers";

const MOCK_STORE_STORAGE_KEY = "mock-store-list";
const MOCK_PRODUCT_STORAGE_KEY = "mock-product-list";
const MOCK_BALANCE_STORAGE_KEY = "mock-stock-balances";
const MOCK_STOCK_TAKE_STORAGE_KEY = "mock-stock-takes";
const DEFAULT_CACHE_TTL_MS = 3000;

async function parseResponse(response) {
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data?.detail || "Request failed.");
        }

        return data;
    }

    if (!response.ok) {
        throw new Error("Request failed.");
    }

    return response.text();
}

function getBrowserStorage() {
    if (typeof window === "undefined") {
        return null;
    }

    return window.sessionStorage;
}

function readMockState(storageKey, fallbackValue) {
    const storage = getBrowserStorage();

    if (!storage) {
        return fallbackValue;
    }

    try {
        const rawValue = storage.getItem(storageKey);
        return rawValue ? JSON.parse(rawValue) : fallbackValue;
    } catch (error) {
        console.warn("Mock storage parsing failed:", error);
        return fallbackValue;
    }
}

function writeMockState(storageKey, value) {
    const storage = getBrowserStorage();

    if (!storage) {
        return;
    }

    storage.setItem(storageKey, JSON.stringify(value));
}

function createMockResponse(payload, status = 200, headers = {}) {
    return new Response(JSON.stringify(payload), {
        status,
        headers: {
            "content-type": "application/json",
            ...headers
        }
    });
}

function delay(ms = 250) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function normalizeText(value) {
    return (value || "").trim().toLowerCase();
}

function getStoresState() {
    const storedStores = readMockState(MOCK_STORE_STORAGE_KEY, null);
    return Array.isArray(storedStores) ? storedStores : [];
}

function persistStoresState(stores) {
    writeMockState(MOCK_STORE_STORAGE_KEY, stores);
}

function getProductsState() {
    const storedProducts = readMockState(MOCK_PRODUCT_STORAGE_KEY, null);
    return Array.isArray(storedProducts) ? storedProducts : [];
}

function persistProductsState(products) {
    writeMockState(MOCK_PRODUCT_STORAGE_KEY, products);
}

function getBalanceState(storeId) {
    const storedBalances = readMockState(MOCK_BALANCE_STORAGE_KEY, {});
    const existingBalance = storedBalances?.[storeId];

    if (existingBalance) {
        return existingBalance;
    }

    return {
        store_id: storeId,
        items: []
    };
}

function persistBalanceState(storeId, balancePayload) {
    const storedBalances = readMockState(MOCK_BALANCE_STORAGE_KEY, {});
    storedBalances[storeId] = balancePayload;
    writeMockState(MOCK_BALANCE_STORAGE_KEY, storedBalances);
}

function getStockTakesState() {
    const storedStockTakes = readMockState(MOCK_STOCK_TAKE_STORAGE_KEY, null);
    return Array.isArray(storedStockTakes) ? storedStockTakes : [];
}

function persistStockTakesState(stockTakes) {
    writeMockState(MOCK_STOCK_TAKE_STORAGE_KEY, stockTakes);
}

class MockInventoryApiAdapter {
    constructor() {
        this.cache = new Map();
        this.cacheTtlMs = DEFAULT_CACHE_TTL_MS;
    }

    getCacheKey(prefix, identifier) {
        return identifier ? `${prefix}:${identifier}` : prefix;
    }

    async withCache(cacheKey, producer) {
        const cachedEntry = this.cache.get(cacheKey);

        if (cachedEntry && Date.now() - cachedEntry.timestamp < this.cacheTtlMs) {
            return cachedEntry.value;
        }

        const value = await producer();
        this.cache.set(cacheKey, { timestamp: Date.now(), value });
        return value;
    }

    invalidateCache(cacheKey) {
        if (!cacheKey) {
            this.cache.clear();
            return;
        }

        this.cache.delete(cacheKey);
    }

    async getAllStores() {
        return this.withCache(this.getCacheKey("stores"), async () => {
            await delay(180);
            const stores = getStoresState();
            return parseResponse(createMockResponse(stores));
        });
    }

    async createStore(storeName) {
        this.invalidateCache(this.getCacheKey("stores"));
        await delay(300);

        const normalizedName = normalizeText(storeName);

        if (!normalizedName) {
            return parseResponse(createMockResponse({ detail: "Store name is required." }, 400));
        }

        const stores = getStoresState();
        const duplicateStore = stores.find((store) => normalizeText(store.store_name || store.name) === normalizedName);

        if (duplicateStore) {
            return parseResponse(createMockResponse({ detail: `Store already exists having name=${storeName}` }, 409));
        }

        const newStore = {
            store_id: Date.now(),
            store_name: normalizedName
        };

        stores.push(newStore);
        persistStoresState(stores);

        return parseResponse(createMockResponse(newStore, 201));
    }

    async getAllProducts() {
        return this.withCache(this.getCacheKey("products"), async () => {
            await delay(180);
            const products = getProductsState();
            return parseResponse(createMockResponse(products));
        });
    }

    async createProduct(productName, unitOrOptions, conversions = []) {
        this.invalidateCache(this.getCacheKey("products"));
        await delay(300);

        let normalizedName = "";
        let normalizedUnit = "";
        let normalizedConversions = [];
        let baseUnit = "";

        if (typeof unitOrOptions === "string") {
            normalizedUnit = normalizeText(unitOrOptions);
            normalizedName = normalizeText(productName);
            normalizedConversions = Array.isArray(conversions) ? conversions : [];
            baseUnit = normalizedUnit;
        } else {
            const incomingOptions = unitOrOptions || {};
            normalizedName = normalizeText(productName);
            normalizedUnit = normalizeText(incomingOptions.baseUnit || incomingOptions.defaultUnit || incomingOptions.unit);
            baseUnit = normalizeText(incomingOptions.baseUnit || incomingOptions.defaultUnit || incomingOptions.unit);
            normalizedConversions = Array.isArray(incomingOptions.conversions) ? incomingOptions.conversions : [];
        }

        if (!normalizedName) {
            return parseResponse(createMockResponse({ detail: "Product name is required." }, 400));
        }

        if (!normalizedUnit) {
            return parseResponse(createMockResponse({ detail: "Product unit is required." }, 400));
        }

        const products = getProductsState();
        const duplicateProduct = products.find((product) => normalizeText(product.product_name || product.name) === normalizedName);

        if (duplicateProduct) {
            return parseResponse(createMockResponse({ detail: `Product already exists having name=${productName}` }, 409));
        }

        const newProduct = {
            product_id: Date.now(),
            product_name: normalizedName,
            default_unit: normalizedUnit,
            base_unit: baseUnit || normalizedUnit,
            unit_conversions: normalizedConversions
        };

        products.push(newProduct);
        persistProductsState(products);

        return parseResponse(createMockResponse(newProduct, 201));
    }

    async submitStockTake({ storeId, productId, targetQuantity, stocktakeDate, remarks = "", recordedBy = 1, unit = null }) {
        this.invalidateCache(this.getCacheKey("stock-takes"));
        this.invalidateCache(this.getCacheKey("stock-balances", Number(storeId)));
        await delay(300);

        const numericStoreId = Number(storeId);
        const numericProductId = Number(productId);
        const quantityValue = Number(targetQuantity);
        const stores = getStoresState();
        const products = getProductsState();

        if (!stores.some((store) => Number(store.store_id ?? store.id) === numericStoreId)) {
            return parseResponse(createMockResponse({ detail: "Store not found." }, 404));
        }

        if (!products.some((product) => Number(product.product_id ?? product.id) === numericProductId)) {
            return parseResponse(createMockResponse({ detail: "Product not found." }, 404));
        }

        if (!Number.isFinite(quantityValue) || quantityValue <= 0) {
            return parseResponse(createMockResponse({ detail: "Quantity must be greater than zero." }, 400));
        }

        const product = products.find((item) => Number(item.product_id ?? item.id) === numericProductId);
        const balancePayload = getBalanceState(numericStoreId);
        const existingItem = balancePayload.items.find((item) => Number(item.product_id ?? item.id) === numericProductId);
        const selectedUnit = normalizeText(unit || product.base_unit || product.default_unit || "pcs") || "pcs";

        const nextItem = {
            product_id: numericProductId,
            product_name: product.product_name,
            available_quantity: quantityValue,
            unit: selectedUnit
        };

        const nextItems = existingItem
            ? balancePayload.items.map((item) => (Number(item.product_id ?? item.id) === numericProductId ? nextItem : item))
            : [...balancePayload.items, nextItem];

        const newStockTake = {
            stocktake_id: Date.now(),
            store_id: numericStoreId,
            product_id: numericProductId,
            target_quantity: quantityValue,
            stocktake_date: stocktakeDate || new Date().toISOString().slice(0, 10),
            remarks,
            recorded_by: recordedBy,
            movement_type: "STOCKTAKE"
        };

        const stockTakes = getStockTakesState();
        stockTakes.push(newStockTake);
        persistStockTakesState(stockTakes);

        persistBalanceState(numericStoreId, {
            ...balancePayload,
            items: nextItems
        });

        return parseResponse(createMockResponse(newStockTake, 201));
    }

    async getStockTakes() {
        return this.withCache(this.getCacheKey("stock-takes"), async () => {
            await delay(180);
            return parseResponse(createMockResponse(getStockTakesState()));
        });
    }

    async getStockBalances(store_id, sort = "alpha", offset = 0, limit = 50) {
        const numericStoreId = Number(store_id);

        return this.withCache(this.getCacheKey("stock-balances", numericStoreId), async () => {
            await delay(180);

            const stores = getStoresState();
            const storeExists = stores.some((store) => Number(store.store_id ?? store.id) === numericStoreId);

            if (!storeExists) {
                return parseResponse(createMockResponse({ detail: "Store not found." }, 404));
            }

            const balancePayload = getBalanceState(numericStoreId);
            const payload = {
                store_id: numericStoreId,
                sort,
                offset,
                limit,
                items: balancePayload.items.slice(offset, offset + limit)
            };

            persistBalanceState(numericStoreId, {
                ...balancePayload,
                items: balancePayload.items
            });

            return parseResponse(createMockResponse(payload));
        });
    }

    async getStockBalanceSummary(store_id) {
        await delay(180);
        const numericStoreId = Number(store_id);
        const balances = getBalanceState(numericStoreId);

        return parseResponse(createMockResponse({
            store_id: numericStoreId,
            total_items: balances.items.length,
            available_quantity: balances.items.reduce((sum, item) => sum + Number(item.available_quantity || 0), 0)
        }));
    }

    clearMockApiState() {
        const storage = getBrowserStorage();

        if (!storage) {
            return;
        }

        storage.removeItem(MOCK_STORE_STORAGE_KEY);
        storage.removeItem(MOCK_PRODUCT_STORAGE_KEY);
        storage.removeItem(MOCK_BALANCE_STORAGE_KEY);
        storage.removeItem(MOCK_STOCK_TAKE_STORAGE_KEY);
        this.invalidateCache();
    }
}

class MainInventoryApiAdapter {
    constructor() {
    }

    async getAllStores() {

    }

    async createStore(storeName) {
    }

    async getAllProducts() {
    }

    async createProduct(productName, baseUnitID, conversionRules = []) {
        const productSKU = getSKU(productName);

        const payload = JSON.stringify({
            "product_name": productName,
            "product_sku": productSKU,
            "base_unit_id": baseUnitID,
            "conversion_rules": conversionRules
        });

        const response = await fetch(`${BACKEND_URL}/product`, {
            "method": "POST",
            "body": payload
        });

        return await response.json();
    }

    async submitStockTake({ storeId, productId, targetQuantity, stocktakeDate, remarks = "", recordedBy = 1, unit = null }) {
    }

    async getStockTakes() {
    }

    async getStockBalances(store_id, sort = "alpha", offset = 0, limit = 50) {
    }

    async getStockBalanceSummary(store_id) {
    }
}

class InventoryApiClient {
    constructor(adapter) {
        this.adapter = adapter;
    }

    getAllStores() {
        return this.adapter.getAllStores();
    }

    createStore(storeName) {
        return this.adapter.createStore(storeName);
    }

    getAllProducts() {
        return this.adapter.getAllProducts();
    }

    createProduct(productName, unitOrOptions, conversions) {
        return this.adapter.createProduct(productName, unitOrOptions, conversions);
    }

    submitStockTake(payload) {
        return this.adapter.submitStockTake(payload);
    }

    getStockTakes() {
        return this.adapter.getStockTakes();
    }

    getStockBalances(store_id, sort = "alpha", offset = 0, limit = 50) {
        return this.adapter.getStockBalances(store_id, sort, offset, limit);
    }

    getStockBalanceSummary(store_id) {
        return this.adapter.getStockBalanceSummary(store_id);
    }

    clearMockApiState() {
        return this.adapter.clearMockApiState();
    }
}

export const inventoryApi = new InventoryApiClient(new MockInventoryApiAdapter());

export function clearMockApiState() {
    return inventoryApi.clearMockApiState();
}

export async function getAllStores() {
    return inventoryApi.getAllStores();
}

export async function createStore(storeName) {
    return inventoryApi.createStore(storeName);
}

export async function getAllProducts() {
    return inventoryApi.getAllProducts();
}

export async function createProduct(productName, unitOrOptions, conversions) {
    return inventoryApi.createProduct(productName, unitOrOptions, conversions);
}

export async function submitStockTake(payload) {
    return inventoryApi.submitStockTake(payload);
}

export async function getStockTakes() {
    return inventoryApi.getStockTakes();
}

export async function getStockBalances(store_id, sort = "alpha", offset = 0, limit = 50) {
    return inventoryApi.getStockBalances(store_id, sort, offset, limit);
}

export async function getStockBalanceSummary(store_id) {
    return inventoryApi.getStockBalanceSummary(store_id);
}

export async function getAllUnits() {
    const response = await fetch(`${BACKEND_URL}/unit/all`);

    if(!response.ok) throw new Error(`Error - ${response.status}. ${await response.json()}`);

    return await response.json();
}

export async function createUnit(unitName, unitSymbol) {
    const response = await fetch(`${BACKEND_URL}/unit`, {
        "method": "POST",
        "body": JSON.stringify({"unit_name": unitName, "unit_symbol": unitSymbol})
    });

    if(!response.ok) throw new Error(`Error - ${response.status}. ${await response.json()}`);

    return await response.json();
}

export { BACKEND_URL, InventoryApiClient, MockInventoryApiAdapter };