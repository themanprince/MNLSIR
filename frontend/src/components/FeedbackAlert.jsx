"use client";

// A small shared alert box for inline success, error, and info feedback.
export default function FeedbackAlert({ kind = "info", title, message }) {
    if (!message) {
        return null;
    }

    const palette = {
        error: "border-rose-200 bg-rose-50 text-rose-700",
        success: "border-emerald-200 bg-emerald-50 text-emerald-700",
        info: "border-blue-200 bg-blue-50 text-blue-700"
    };

    return (
        <div className={`rounded-2xl border px-4 py-3 text-sm ${palette[kind] || palette.info}`}>
            {title ? <p className="font-semibold">{title}</p> : null}
            <p className={title ? "mt-1" : ""}>{message}</p>
        </div>
    );
}
