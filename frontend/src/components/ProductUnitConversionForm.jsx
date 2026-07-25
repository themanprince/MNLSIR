"use client";

// Shared UI for capturing a product's base unit and optional conversion rules.
export default function ProductUnitConversionForm({
    baseUnitID,
    onBaseUnitIDChange,
    conversionRules,
    updateConversionRule,
    addConversionRule,
    removeConversionRule,
    allowedUnits,
    unitLabel,
    unitPlaceholder,
    conversionLabel,
    conversionDescription,
    addConversionLabel,
    conversionUnitLabel,
    conversionAmountLabel,
    noConversionsText,
    helperText
}) {
    return (
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h3 className="text-sm font-semibold text-slate-900">{conversionLabel}</h3>
                    <p className="text-sm text-slate-500">{conversionDescription}</p>
                </div>
            </div>

            <div className="mt-4 space-y-3">
                <div className="space-y-2">
                    <label htmlFor="product-unit" className="text-sm font-semibold text-slate-700">
                        {unitLabel}
                    </label>
                    <select
                        required
                        id="product-unit"
                        value={baseUnitID}
                        onChange={onBaseUnitIDChange}
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                    >
                        <option value="">{unitPlaceholder}</option>
                        {allowedUnits.map((unit) => (
                            <option key={unit["unit_symbol"]} value={unit["unit_id"]}>
                                {`${unit["unit_name"]} (${unit["unit_symbol"]})`}
                            </option>
                        ))}
                    </select>
                </div>

                {conversionRules.map((rule) => (
                    <div key={rule.id} className="grid gap-3 md:grid-cols-[1fr_0.8fr_auto]">
                        <div className="space-y-1">
                            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                                {conversionUnitLabel}
                            </label>
                            <select
                                value={rule["unit_id"]}
                                onChange={(event) => updateConversionRule(rule.id, "unit_id", event.target.value)}
                                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                            >
                                <option value="">{unitPlaceholder}</option>
                                {allowedUnits.filter((unit) => Number(unit.unitID) != Number(baseUnitID)).map((unit) => (
                                    <option key={unit["unit_symbol"]} value={unit["unit_id"]}>
                                        {`${unit["unit_name"]} (${unit["unit_symbol"]})`}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                                {conversionAmountLabel}
                            </label>
                            <input
                                type="number"
                                min="0.0001"
                                step="0.0001"
                                value={rule.multiplierToBase}
                                onChange={(event) => updateConversionRule(rule.id, "multiplierToBase", event.target.value)}
                                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                            />
                        </div>
                        <button
                            type="button"
                            onClick={() => removeConversionRule(rule.id)}
                            className="self-end rounded-2xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 transition hover:border-rose-200 hover:text-rose-600"
                        >
                            Remove
                        </button>
                    </div>
                ))}
                
                {conversionRules.length === 0 ? (
                    <p className="text-sm text-slate-500">{noConversionsText}</p>
                ) : null}

                <div className="w-full flex flex-row justify-end">
                    <button
                        type="button"
                        onClick={addConversionRule}
                        className="rounded-full border border-blue-200 bg-blue-500 px-3 py-2 text-sm font-semibold text-white-700 transition hover:border-blue-300 hover:bg-blue-100"
                    >
                        {addConversionLabel}
                    </button>
                </div>

            </div>

            {helperText ? <p className="mt-4 text-sm text-slate-500">{helperText}</p> : null}
        </div>
    );
}
