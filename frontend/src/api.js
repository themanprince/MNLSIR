import { BACKEND_URL } from "@/CONSTANTS";

const MOCK_STORE_STORAGE_KEY = "mock-store-list";
const MOCK_BALANCE_STORAGE_KEY = "mock-stock-balances";

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

    if (Array.isArray(storedStores) && storedStores.length > 0) {
        return storedStores;
    }

    const seedStores = getSeedStores();
    writeMockState(MOCK_STORE_STORAGE_KEY, seedStores);
    return seedStores;
}

function persistStoresState(stores) {
    writeMockState(MOCK_STORE_STORAGE_KEY, stores);
}

function getBalanceState(storeId) {
    const storedBalances = readMockState(MOCK_BALANCE_STORAGE_KEY, {});
    const existingBalance = storedBalances?.[storeId];

    if (existingBalance) {
        return existingBalance;
    }

    return {
        store_id: storeId,
        items: [
            {
                product_name: "Sample product",
                available_quantity: 0,
                unit: "pcs"
            }
        ]
    };
}

function persistBalanceState(storeId, balancePayload) {
    const storedBalances = readMockState(MOCK_BALANCE_STORAGE_KEY, {});
    storedBalances[storeId] = balancePayload;
    writeMockState(MOCK_BALANCE_STORAGE_KEY, storedBalances);
}

export function clearMockApiState() {
    const storage = getBrowserStorage();

    if (!storage) {
        return;
    }

    storage.removeItem(MOCK_STORE_STORAGE_KEY);
    storage.removeItem(MOCK_BALANCE_STORAGE_KEY);
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