import React, { useState } from "react";
import { Search } from "lucide-react";
import HomeScreen from "./pages/HomeScreen";
import ClientView from "./pages/ClientView";
import { useMe } from "./hooks/useApi";
import { fmtCpf, cleanCpf } from "./hooks/useFormatters";

export default function App() {
  const [cpf, setCpf] = useState<string | null>(null);
  const { data: me } = useMe();

  return (
    <div className="h-screen flex flex-col overflow-hidden font-sans">

      {/* TOPBAR — só aparece quando há cliente ativo */}
      {cpf && (
        <header className="h-13 bg-white border-b border-gray-200 px-5 flex items-center gap-3 shrink-0 shadow-sm z-10">
          {/* Logo */}
          <img
            src="/logo.png"
            alt="CGI Bemol"
            className="h-7 object-contain"
            onError={(e) => {
              const img = e.currentTarget as HTMLImageElement;
              img.style.display = "none";
              const fallback = img.nextElementSibling as HTMLElement;
              if (fallback) fallback.style.display = "flex";
            }}
          />
          <div
            className="w-7 h-7 bg-pip-500 rounded-lg text-white font-bold text-sm items-center justify-center hidden"
            aria-hidden
          >
            B
          </div>

          <div className="w-px h-5 bg-gray-200 mx-1" />

          {/* Busca rápida */}
          <TopbarSearch onSelect={setCpf} />

          {/* Usuário */}
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[11px] text-gray-400 hidden sm:block">
              {me?.email || ""}
            </span>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pip-500 to-purple-500 text-white text-[11px] font-bold flex items-center justify-center">
              {me?.initials ?? "?"}
            </div>
          </div>
        </header>
      )}

      {/* MAIN CONTENT */}
      <main className="flex-1 overflow-hidden flex flex-col">
        {!cpf
          ? <HomeScreen onSelect={setCpf} />
          : <ClientView cpf={cpf} />
        }
      </main>
    </div>
  );
}

// ── Topbar inline search ───────────────────────────────────────────────────────
function TopbarSearch({ onSelect }: { onSelect: (cpf: string) => void }) {
  const [val, setVal] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const c = cleanCpf(val.trim());
    if (c.length === 11) onSelect(c);
  }

  return (
    <form onSubmit={handleSubmit}
      className="flex items-center gap-1.5 bg-gray-100 border border-gray-200 rounded-xl px-3 py-1.5 focus-within:border-pip-400 focus-within:ring-2 focus-within:ring-pip-100 transition-all max-w-[320px]">
      <Search size={13} className="text-gray-400 shrink-0" />
      <input
        value={val}
        onChange={e => setVal(e.target.value)}
        placeholder="Buscar outro cliente..."
        className="bg-transparent outline-none text-[12px] text-gray-800 placeholder-gray-400 w-full"
      />
      <button type="submit"
        className="text-[11px] font-semibold text-pip-600 hover:text-pip-700 shrink-0">
        Buscar
      </button>
    </form>
  );
}
