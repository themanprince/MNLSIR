import { BACKEND_URL } from "@/CONSTANTS";

const MOCK_STORE_STORAGE_KEY = "mock-store-list";
const MOCK_PRODUCT_STORAGE_KEY = "mock-product-list";
const MOCK_BALANCE_STORAGE_KEY = "mock-stock-balances";
const MOCK_STOCK_TAKE_STORAGE_KEY = "mock-stock-takes";

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

function delay(ms = 450) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function getSeedStores() {
    return [
        { store_id: 1, store_name: "lagos main store" },
        { store_id: 2, store_name: "abuja branch" }
    ];
}

function getStoresState() {
    const storedStores = readMockState(MOCK_STORE_STORAGE_KEY, null);

    return storedStores || [];
    
}

function persistStoresState(stores) {
    writeMockState(MOCK_STORE_STORAGE_KEY, stores);
}

function getProductsState() {
    const storedProducts = readMockState(MOCK_PRODUCT_STORAGE_KEY, null);

    if (Array.isArray(storedProducts)) {
        return storedProducts;
    }

    return [];
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

    if (Array.isArray(storedStockTakes)) {
        return storedStockTakes;
    }

    return [];
}

function persistStockTakesState(stockTakes) {
    writeMockState(MOCK_STOCK_TAKE_STORAGE_KEY, stockTakes);
}

export function clearMockApiState() {
    const storage = getBrowserStorage();

    if (!storage) {
        return;
    }

    storage.removeItem(MOCK_STORE_STORAGE_KEY);
    storage.removeItem(MOCK_PRODUCT_STORAGE_KEY);
    storage.removeItem(MOCK_BALANCE_STORAGE_KEY);
    storage.removeItem(MOCK_STOCK_TAKE_STORAGE_KEY);
}

export async function getAllStores() {
    await delay(350);

    const stores = getStoresState();
    return parseResponse(createMockResponse(stores));
}

export async function createStore(storeName) {
    await delay(600);

    const normalizedName = (storeName || "").trim().toLowerCase();

    if (!normalizedName) {
        return parseResponse(createMockResponse({ detail: "Store name is required." }, 400));
    }

    const stores = getStoresState();
    const duplicateStore = stores.find((store) => store.store_name === normalizedName);

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

export async function getAllProducts() {
    await delay(350);

    const products = getProductsState();
    return parseResponse(createMockResponse(products));
}

export async function createProduct(productName, unit) {
    await delay(600);

    const normalizedName = (productName || "").trim().toLowerCase();
    const normalizedUnit = (unit || "").trim().toLowerCase();

    if (!normalizedName) {
        return parseResponse(createMockResponse({ detail: "Product name is required." }, 400));
    }

    if (!normalizedUnit) {
        return parseResponse(createMockResponse({ detail: "Product unit is required." }, 400));
    }

    const products = getProductsState();
    const duplicateProduct = products.find((product) => product.product_name === normalizedName);

    if (duplicateProduct) {
        return parseResponse(createMockResponse({ detail: `Product already exists having name=${productName}` }, 409));
    }

    const newProduct = {
        product_id: Date.now(),
        product_name: normalizedName,
        default_unit: normalizedUnit
    };

    products.push(newProduct);
    persistProductsState(products);

    return parseResponse(createMockResponse(newProduct, 201));
}

export async function submitStockTake({ storeId, productId, targetQuantity, stocktakeDate, remarks = "", recordedBy = 1 }) {
    await delay(600);

    const numericStoreId = Number(storeId);
    const numericProductId = Number(productId);
    const quantityValue = Number(targetQuantity);
    const stores = getStoresState();
    const products = getProductsState();

    if (!stores.some((store) => store.store_id === numericStoreId)) {
        return parseResponse(createMockResponse({ detail: "Store not found." }, 404));
    }

    if (!products.some((product) => product.product_id === numericProductId)) {
        return parseResponse(createMockResponse({ detail: "Product not found." }, 404));
    }

    if (!Number.isFinite(quantityValue) || quantityValue < 0) {
        return parseResponse(createMockResponse({ detail: "Quantity must be zero or greater." }, 400));
    }

    const product = products.find((item) => item.product_id === numericProductId);
    const balancePayload = getBalanceState(numericStoreId);
    const existingItem = balancePayload.items.find((item) => item.product_id === numericProductId);

    const nextItem = {
        product_id: numericProductId,
        product_name: product.product_name,
        available_quantity: quantityValue,
        unit: product.default_unit || "pcs"
    };

    const nextItems = existingItem
        ? balancePayload.items.map((item) => (item.product_id === numericProductId ? nextItem : item))
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

export async function getStockTakes() {
    await delay(350);

    return parseResponse(createMockResponse(getStockTakesState()));
}

export async function getStockBalances(store_id, sort = "alpha", offset = 0, limit = 50) {
    await delay(400);

    const numericStoreId = Number(store_id);
    const stores = getStoresState();
    const storeExists = stores.some((store) => store.store_id === numericStoreId);

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
}

export async function getStockBalanceSummary(store_id) {
    await delay(350);

    const numericStoreId = Number(store_id);
    const balances = getBalanceState(numericStoreId);

    return parseResponse(createMockResponse({
        store_id: numericStoreId,
        total_items: balances.items.length,
        available_quantity: balances.items.reduce((sum, item) => sum + Number(item.available_quantity || 0), 0)
    }));
}

export { BACKEND_URL };