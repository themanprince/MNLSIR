export function getSKU(productName) {
    return String(productName).toLowerCase().split("").join("_");
}