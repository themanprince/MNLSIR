"use client";

// A simple two-column layout wrapper used by the inventory pages.
export default function PageSection({ children, className = "" }) {
    return <section className={`grid gap-8 xl:grid-cols-[1.05fr_0.95fr] ${className}`.trim()}>{children}</section>;
}
