import { BACKEND_URL } from "@/CONSTANTS";

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

export async function getAllStores() {
    const response = await fetch(`${BACKEND_URL}/store/all`, {
        method: "GET"
    });

    return parseResponse(response);
}

export async function createStore(storeName) {
    const response = await fetch(`${BACKEND_URL}/store/${encodeURIComponent(storeName)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    });

    return parseResponse(response);
}

export async function getStockBalances(store_id, sort = "alpha", offset = 0, limit = 50) {
    const response = await fetch(`${BACKEND_URL}/ledger/stock-balances/${store_id}?sort=${sort}&offset=${offset}&limit=${limit}`, {
        method: "GET"
    });

    return parseResponse(response);
}