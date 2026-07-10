"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { APP_NAME, APP_SHORT_NAME, APP_SUBTITLE } from "@/CONSTANTS";

export function SidebarNav({navigation_routes}) {
    const pathname = usePathname();

    return (
        <aside className="w-68 bg-slate-900 text-slate-300 flex flex-col justify-between hidden md:flex h-full shadow-2xl relative z-20">
            <div className="p-6">
                <div className="flex items-center gap-3 pb-6 border-b border-slate-800">
                    <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/30">
                        {APP_SHORT_NAME.slice(0, 1)}
                    </div>
                    <div>
                        <h1 className="text-sm font-bold text-white tracking-wide uppercase">{APP_NAME}</h1>
                        <p className="text-xs text-slate-500 font-medium">{APP_SUBTITLE}</p>
                    </div>
                </div>

                <nav className="mt-8 space-y-1.5">
                    {navigation_routes.map((route) => {
                        const isActive = pathname === route.href;

                        return (
                            <Link
                                key={route.href}
                                href={route.href}
                                className={`flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 group relative ${
                                    isActive
                                        ? "text-white bg-gradient-to-r from-slate-800 to-slate-800/50 shadow-inner"
                                        : "hover:text-white hover:bg-slate-800/40"
                                }`}
                            >
                                {isActive && (
                                    <span className="absolute left-0 top-3 bottom-3 w-1 bg-gradient-to-b from-blue-400 to-indigo-500 rounded-r-md" />
                                )}

                                <span className={`transition-colors ${isActive ? "text-blue-400" : "text-slate-500 group-hover:text-slate-300"}`}>
                                    {route.icon}
                                </span>

                                {route.label}
                            </Link>
                        );
                    })}
                </nav>
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-semibold text-slate-500 tracking-wider uppercase">Engine Live</span>
            </div>
        </aside>
    );
}