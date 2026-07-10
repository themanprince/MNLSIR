"use client";

// Shared wrapper for the main content panels used across the inventory views.
export default function SectionCard({ title, description, children, className = "" }) {
    return (
        <div className={`rounded-3xl border border-slate-200/70 bg-white p-8 shadow-sm ${className}`.trim()}>
            {(title || description) ? (
                <div className="mb-6">
                    {title ? <h2 className="text-xl font-semibold text-slate-900">{title}</h2> : null}
                    {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
                </div>
            ) : null}
            {children}
        </div>
    );
}
