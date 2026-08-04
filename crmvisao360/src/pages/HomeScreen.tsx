import React, { useState, useRef } from "react";
import { Search } from "lucide-react";
import { Spinner } from "../components/ui";
import { useBusca } from "../hooks/useApi";
import { fmtCpf, cleanCpf } from "../hooks/useFormatters";
import type { Cliente, ClienteResumo } from "../types/api";

interface Props {
  onSelect: (cpf: string) => void;
}

export default function HomeScreen({ onSelect }: Props) {
  const [input, setInput]     = useState("");
  const [query, setQuery]     = useState("");
  const [enabled, setEnabled] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data, isFetching, isError, error } = useBusca(query, enabled);

  function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    const q = input.trim();
    if (!q) return;
    setQuery(q);
    setEnabled(true);
  }

  // Auto-select when CPF found directly
  React.useEffect(() => {
    if (data?.tipo === "cpf") {
      onSelect((data.resultado as Cliente).cpf);
    }
  }, [data, onSelect]);

  const lista = data?.tipo === "lista" ? (data.resultado as ClienteResumo[]) : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-pip-50 flex flex-col items-center justify-center px-6">

      {/* Logo — adicione logo.png na raiz do projeto */}
      <div className="mb-8 animate-fadeIn">
        <img
          src="/logo.png"
          alt="CGI Bemol"
          className="h-16 object-contain drop-shadow-sm"
          onError={(e) => {
            // fallback se logo não existir ainda
            (e.currentTarget as HTMLImageElement).style.display = "none";
          }}
        />
        <p className="text-gray-400 text-sm text-center mt-3 font-medium">
          Empréstimo com Garantia de Imóvel
        </p>
      </div>

      {/* Search box */}
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-lg animate-slideUp"
      >
        <div className="relative flex items-center bg-white border border-gray-200 rounded-2xl shadow-md shadow-pip-100/40 focus-within:border-pip-500 focus-within:ring-4 focus-within:ring-pip-500/10 transition-all">
          <Search className="absolute left-4 text-gray-400 shrink-0" size={18} />
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="CPF ou nome do cliente..."
            autoFocus
            className="flex-1 bg-transparent outline-none text-[15px] text-gray-900 placeholder-gray-400 py-4 pl-11 pr-4 font-medium"
          />
          <button
            type="submit"
            disabled={isFetching || !input.trim()}
            className="m-1.5 h-9 px-5 bg-pip-500 hover:bg-pip-600 active:bg-pip-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-all flex items-center gap-2 shrink-0"
          >
            {isFetching ? <Spinner size={14} /> : null}
            {isFetching ? "Buscando" : "Buscar"}
          </button>
        </div>

        {/* Hint */}
        <p className="text-center text-[11px] text-gray-400 mt-3">
          Ex:{" "}
          <button
            type="button"
            className="text-pip-500 font-semibold hover:underline"
            onClick={() => { setInput("389.448.712-72"); inputRef.current?.focus(); }}
          >
            389.448.712-72
          </button>
          {" "}ou{" "}
          <button
            type="button"
            className="text-pip-500 font-semibold hover:underline"
            onClick={() => { setInput("João Silva"); inputRef.current?.focus(); }}
          >
            João Silva
          </button>
        </p>
      </form>

      {/* Overlay de busca */}
      {isFetching && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center animate-fadeIn">
          <div className="bg-white rounded-2xl px-12 py-10 flex flex-col items-center gap-4 shadow-2xl">
            <Spinner size={36} />
            <div>
              <p className="text-[15px] font-semibold text-gray-900 text-center">
                Buscando cliente
              </p>
              <p className="text-[12px] text-gray-400 text-center mt-1">
                Consultando a base de dados...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Erro da API */}
      {isError && !isFetching && (
        <div className="mt-6 w-full max-w-lg animate-slideUp">
          <div className="bg-white border border-red-200 rounded-2xl shadow-sm p-8 flex flex-col items-center gap-3 text-center">
            <div className="w-14 h-14 rounded-full bg-red-50 flex items-center justify-center text-2xl">
              🔍
            </div>
            <p className="text-[15px] font-bold text-gray-900">
              {error?.message?.includes("não encontrado")
                ? "Cliente não encontrado"
                : "Erro na busca"}
            </p>
            <p className="text-[12px] text-gray-500 max-w-[300px]">
              {error?.message?.includes("não encontrado") ? (
                <>
                  Nenhum registro para{" "}
                  <strong className="font-mono text-pip-600 bg-pip-50 px-1.5 py-0.5 rounded">
                    {cleanCpf(input).length === 11 ? fmtCpf(cleanCpf(input)) : input}
                  </strong>
                </>
              ) : (
                error?.message ?? "Tente novamente."
              )}
            </p>
            <button
              onClick={() => { setEnabled(false); setInput(""); inputRef.current?.focus(); }}
              className="mt-2 px-5 py-2 bg-pip-500 text-white text-sm font-semibold rounded-xl hover:bg-pip-600 transition-colors"
            >
              Tentar novamente
            </button>
          </div>
        </div>
      )}

      {/* Lista de resultados (busca por nome) */}
      {lista.length > 0 && !isFetching && (
        <div className="mt-4 w-full max-w-lg animate-slideUp">
          <p className="text-[11px] text-gray-400 mb-2 px-1">
            {lista.length} resultado{lista.length > 1 ? "s" : ""} — clique para abrir
          </p>
          <div className="bg-white border border-gray-200 rounded-2xl shadow-md overflow-hidden">
            {lista.map((r, i) => (
              <button
                key={r.cpf}
                onClick={() => onSelect(r.cpf)}
                className={`w-full text-left px-4 py-3 hover:bg-pip-50 transition-colors flex items-center gap-3 ${
                  i > 0 ? "border-t border-gray-100" : ""
                }`}
              >
                <div className="w-9 h-9 rounded-xl bg-pip-50 text-pip-600 font-bold text-sm flex items-center justify-center shrink-0">
                  {r.nome_cliente.split(" ").slice(0, 2).map(p => p[0]).join("").toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-gray-900 truncate">
                    {r.nome_cliente}
                  </p>
                  <p className="text-[11px] text-gray-400 mt-0.5">
                    {fmtCpf(r.cpf)} · {r.responsavel || "—"} · {r.telefone || "—"}
                  </p>
                </div>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                  r.fase_ativa
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : "bg-gray-100 text-gray-500 border-gray-200"
                }`}>
                  {r.fase_atual}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
