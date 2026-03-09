import { ReactNode } from "react";
import { BrainCircuit, Github, Cpu } from "lucide-react";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a14]">
      {/* Top bar */}
      <header className="border-b border-surface-border bg-surface-card/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center glow-brand">
              <BrainCircuit size={18} className="text-white" />
            </div>
            <span className="font-semibold text-white text-sm tracking-wide">
              AI Employee Vault
            </span>
            <span className="badge bg-brand-900/60 text-brand-300 border border-brand-800">
              Platinum
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-1.5">
              <Cpu size={12} />
              <span>claude-sonnet-4-6</span>
            </div>
            <span>Hackathon 0</span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1400px] mx-auto px-6 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-border mt-16 py-4 text-center text-xs text-slate-600">
        AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0 · Powered by Claude · Personal AI Employee
      </footer>
    </div>
  );
}
