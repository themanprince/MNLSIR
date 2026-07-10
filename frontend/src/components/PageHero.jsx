"use client";

// Shared hero section used across the main inventory pages.
export default function PageHero({
    badge,
    title,
    description,
    summaryValue,
    summaryLabel,
    children,
    className = ""
}) {
    return (
        <section className={`rounded-3xl border border-slate-200/70 bg-white/90 p-8 shadow-[0_25px_80px_-30px_rgba(15,23,42,0.25)] backdrop-blur ${className}`.trim()}>
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                <div className="max-w-2xl space-y-3">
                    {badge ? (
                        <span className="inline-flex w-fit items-center rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-blue-600">
                            {badge}
                        </span>
                    ) : null}
                    <div className="space-y-2">
                        {title ? <h1 className="text-3xl font-semibold tracking-tight text-slate-900">{title}</h1> : null}
                        {description ? <p className="text-sm leading-7 text-slate-600">{description}</p> : null}
                    </div>
                    {children}
                </div>

                {summaryValue || summaryLabel ? (
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 shadow-sm">
                        {summaryValue ? <p className="font-semibold text-slate-900">{summaryValue}</p> : null}
                        {summaryLabel ? <p>{summaryLabel}</p> : null}
                    </div>
                ) : null}
            </div>
        </section>
    );
}
