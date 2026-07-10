"use client";

export default function StoreCreateInfoPanel() {
    return (
        <aside className="rounded-3xl border border-slate-200/70 bg-slate-950 p-8 text-white shadow-[0_30px_80px_-35px_rgba(2,6,23,0.9)]">
            <div className="space-y-4">
                <div className="inline-flex rounded-full border border-white/10 bg-white/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-300">
                    What happens next
                </div>
                <h2 className="text-xl font-semibold">From here, you can immediately use the store in inventory workflows.</h2>
                <ul className="space-y-3 text-sm leading-7 text-slate-300">
                    <li className="flex gap-3">
                        <span className="mt-2 h-2.5 w-2.5 rounded-full bg-blue-400" />
                        Track stock receipts and issues in one place.
                    </li>
                    <li className="flex gap-3">
                        <span className="mt-2 h-2.5 w-2.5 rounded-full bg-blue-400" />
                        Review balances and stock take reports with less effort.
                    </li>
                    <li className="flex gap-3">
                        <span className="mt-2 h-2.5 w-2.5 rounded-full bg-blue-400" />
                        Keep store records organized as your operations grow.
                    </li>
                </ul>
            </div>
        </aside>
    );
}
