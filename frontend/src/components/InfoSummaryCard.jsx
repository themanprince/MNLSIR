"use client";

// Small summary pill used in the top section of the dashboards.
export default function InfoSummaryCard({ value, label, tone = "default" }) {
    const toneClasses = {
        default: "border-slate-200 bg-slate-50 text-slate-600",
        success: "border-emerald-100 bg-emerald-50 text-emerald-700"
    };

    return (
        <div className={`rounded-2xl border px-4 py-3 text-sm shadow-sm ${toneClasses[tone] || toneClasses.default}`}>
            {value ? <p className="font-semibold text-slate-900">{value}</p> : null}
            {label ? <p>{label}</p> : null}
        </div>
    );
}
