export const BACKEND_URL = "http://localhost:8000";

export const APP_NAME = "Mazuka";
export const APP_SUBTITLE = "Nigeria Limited";
export const APP_SHORT_NAME = "MNLSIR";

export const CREATE_STORE_COPY = {
    heading: "Create a new store",
    description: "Add a store to begin tracking stock movements, reconciliations, and balances from one consistent workspace.",
    inputLabel: "Store name",
    inputPlaceholder: "e.g. Lagos Main Store",
    submitLabel: "Create store",
    helperText: "Store names are used as the unique identifier in the inventory workflow.",
    successTitle: "Store created successfully",
    successMessage: "The new store is now ready for stock operations.",
    errorFallback: "We could not create that store. Please try again."
};

export const NAVIGATION_ROUTES = [
    {
        label: "Stock Balances",
        href: "/stock-balances",
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
        )
    },
    {
        label: "Create Store",
        href: "/stores/create",
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
        )
    }
];
