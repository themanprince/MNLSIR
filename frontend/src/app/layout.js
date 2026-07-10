import "./globals.css";
import { NAVIGATION_ROUTES } from "@/CONSTANTS";
import {SidebarNav} from "@/components/SidebarNav";

export const metadata = {
  title: "Mazuka Nigeria Limited",
  description: "System for Integrated Records"
};

export default function RootLayout({children}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased font-sans">
        <div className="flex h-screen w-full overflow-hidden">
          
          <SidebarNav navigation_routes={NAVIGATION_ROUTES}/>

          <div className="flex flex-col flex-1 min-w-0 bg-gradient-to-b from-slate-50 to-slate-100 overflow-y-auto">

            <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200/80 flex items-center justify-between px-8 sticky top-0 z-10 shadow-sm">
              <div className="text-xs font-bold uppercase tracking-widest text-slate-400">MNLSIR</div>
              <div className="h-9 w-9 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 text-sm font-semibold shadow-sm hover:bg-slate-200/50 transition cursor-pointer">
                AD
              </div>
            </header>
            
            <main className="p-8 max-w-7xl w-full mx-auto">
              {children}
            </main>
            
          </div>
        </div>
      </body>
    </html>
  );
}