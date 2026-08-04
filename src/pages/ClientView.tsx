import { useState } from "react";
import { ExternalLink, ChevronDown, ChevronRight, AlertTriangle, Clock } from "lucide-react";
import { clsx } from "clsx";
import {
  useCliente, useContratos, useParcelasResumo,
  useParcelasDetalhe, useDocumentos, useAtendimentos,
} from "../hooks/useApi";
import { fmtBrl, fmtDate, fmtCpf, initials, faseColor } from "../hooks/useFormatters";
import { Badge, Field, SectionCard, KpiCard, Spinner, Empty } from "../components/ui";

// ── Tabs ──────────────────────────────────────────────────────────────────────
const TABS = ["Visão 360°", "Contratos", "Parcelas", "Documentos", "Atendimento"] as const;
type Tab = typeof TABS[number];

// ── Main ──────────────────────────────────────────────────────────────────────
export default function ClientView({ cpf }: { cpf: string }) {
  const [tab, setTab] = useState<Tab>("Visão 360°");

  const { data: cliente,     isLoading: loadingC  } = useCliente(cpf);
  const { data: contratos,   isLoading: loadingCo } = useContratos(cpf);
  const { data: parResumo } = useParcelasResumo(cpf);
  const { data: parDetalhe,  isLoading: loadingPd } = useParcelasDetalhe(cpf);
  const { data: documentos,  isLoading: loadingD  } = useDocumentos(cpf);
  const { data: atendimentos,isLoading: loadingAt } = useAtendimentos(cpf);

  if (loadingC) {
    return (
      <div className="flex-1 flex items-center justify-center gap-3 text-gray-500 text-sm">
        <Spinner /> Carregando dados do cliente...
      </div>
    );
  }
  if (!cliente) return null;

  const at         = atendimentos?.[0];
  const emAtraso   = (parResumo?.em_atraso ?? 0) > 0;
  const cardParado = (at?.dias_sem_atualizacao ?? 0) > 7;
  const faseColor_ = faseColor(cliente.fase_atual, cliente.fase_ativa);
  const urlPipefy  = at?.url_card_pipefy ?? "#";

  const totalFinanciado = (contratos ?? []).reduce(
    (s, c) => s + (c.valor_financiado ?? 0), 0
  );

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">

      {/* ── CLIENT HEADER ── */}
      <div className="bg-white border-b border-gray-200 px-6 pt-5 pb-0 shrink-0">
        <div className="flex items-start gap-4 mb-4">
          {/* Avatar */}
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pip-500 to-purple-500 text-white font-bold text-lg flex items-center justify-center shrink-0">
            {initials(cliente.nome_cliente)}
          </div>

          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold text-gray-900 leading-tight mb-1.5">
              {cliente.nome_cliente.toUpperCase()}
            </h1>
            <div className="flex flex-wrap gap-1.5">
              <Badge color="pip">CPF: {fmtCpf(cpf)}</Badge>
              <Badge color={faseColor_ === "green" ? "green" : "gray"}>
                {cliente.fase_atual}
              </Badge>
              <Badge color={cliente.eh_cliente ? "blue" : "gray"}>
                {cliente.eh_cliente ? "Cliente Bemol" : "Prospect"}
              </Badge>
              {cliente.pep?.toUpperCase() === "SIM" && (
                <Badge color="red">⚠ PEP</Badge>
              )}
            </div>
            <p className="text-[11px] text-gray-400 mt-1.5">
              {cliente.telefone && <>📞 {cliente.telefone}&nbsp;&nbsp;</>}
              {cliente.email && <>✉ {cliente.email}&nbsp;&nbsp;</>}
              {cliente.cidade && <>{cliente.cidade}{cliente.estado ? ` / ${cliente.estado}` : ""}</>}
            </p>
          </div>

          <a
            href={urlPipefy}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-pip-500 hover:bg-pip-600 text-white text-xs font-semibold rounded-xl transition-colors shrink-0"
          >
            <ExternalLink size={13} />
            Pipefy
          </a>
        </div>

        {/* KPI strip */}
        <div className="grid grid-cols-6 gap-px bg-gray-200 border-t border-gray-200 -mx-6">
          <KpiCard label="Financiado" value={fmtBrl(totalFinanciado)}
            sub={`${contratos?.length ?? 0} contrato(s)`} color="pip" />
          <KpiCard label="Em Atraso"
            value={fmtBrl(parResumo?.saldo_em_atraso)}
            sub={`${parResumo?.em_atraso ?? 0} parcela(s)`}
            color={emAtraso ? "red" : "green"} />
          <KpiCard label="A Vencer 30d"
            value={fmtBrl(parResumo?.total_a_vencer)}
            sub={`${parResumo?.vence_30d ?? 0} parcela(s)`} color="amber" />
          <KpiCard label="Total Pago"
            value={fmtBrl(parResumo?.total_pago)}
            sub={`Adimpl.: ${parResumo?.taxa_adimplencia ?? 0}%`} color="green" />
          <KpiCard label="Score Risco"
            value={cliente.score_risco ?? "—"}
            sub={`Renda: ${fmtBrl(cliente.renda_mensal)}`} color="pip" />
          <KpiCard label="Documentos"
            value={documentos?.length ?? "—"}
            sub={`Pessoas: ${new Set(documentos?.map(d => d.id_card_pessoas)).size}`} />
        </div>

        {/* Tabs */}
        <div className="flex gap-1.5 pt-2 -mx-6 px-6 overflow-x-auto">
          {TABS.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={clsx(
                "px-3 py-2 text-[11px] font-semibold rounded-t-lg border-b-2 whitespace-nowrap transition-all",
                tab === t
                  ? "border-pip-500 text-pip-600 bg-pip-50"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50"
              )}>
              {t}
              {t === "Contratos"   && <span className="ml-1 opacity-60">({contratos?.length ?? "…"})</span>}
              {t === "Parcelas"    && <span className="ml-1 opacity-60">({parDetalhe?.length ?? "…"})</span>}
              {t === "Documentos"  && <span className="ml-1 opacity-60">({documentos?.length ?? "…"})</span>}
              {t === "Atendimento" && <span className="ml-1 opacity-60">({atendimentos?.length ?? "…"})</span>}
            </button>
          ))}
        </div>
      </div>

      {/* ── PANELS ── */}
      <div className="flex-1 overflow-y-auto bg-gray-50 p-5">

        {/* Alerts */}
        {(emAtraso || cardParado) && (
          <div className="flex flex-col gap-2 mb-4">
            {emAtraso && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-xl px-4 py-2.5 text-red-700 text-[12px] font-medium">
                <AlertTriangle size={14} />
                {parResumo?.em_atraso} parcela(s) em atraso — {fmtBrl(parResumo?.saldo_em_atraso)}
              </div>
            )}
            {cardParado && (
              <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-xl px-4 py-2.5 text-amber-700 text-[12px] font-medium">
                <Clock size={14} />
                Card sem atualização há {at?.dias_sem_atualizacao} dias
              </div>
            )}
          </div>
        )}

        {tab === "Visão 360°" && (
          <Tab360 cliente={cliente} at={at} parResumo={parResumo}
            contratos={contratos} documentos={documentos} urlPipefy={urlPipefy} />
        )}
        {tab === "Contratos" && (
          <TabContratos contratos={contratos} loading={loadingCo} />
        )}
        {tab === "Parcelas" && (
          <TabParcelas resumo={parResumo} detalhe={parDetalhe} loading={loadingPd} />
        )}
        {tab === "Documentos" && (
          <TabDocumentos docs={documentos} loading={loadingD} />
        )}
        {tab === "Atendimento" && (
          <TabAtendimento atendimentos={atendimentos} loading={loadingAt} />
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB: VISÃO 360
// ─────────────────────────────────────────────────────────────────────────────
function Tab360({ cliente, at, parResumo, contratos, documentos, urlPipefy }: any) {
  return (
    <div className="grid grid-cols-[300px_1fr] gap-4">
      {/* Coluna esq */}
      <div className="flex flex-col gap-4">
        <SectionCard title="Dados Pessoais">
          <div className="p-4 grid grid-cols-2 gap-3">
            <Field label="Nome"         value={cliente.nome_cliente} />
            <Field label="CPF"          value={fmtCpf(cliente.cpf)} />
            <Field label="Profissão"    value={cliente.profissao} />
            <Field label="Renda Mensal" value={fmtBrl(cliente.renda_mensal)} highlight="pip" />
            <Field label="Renda Apurada" value={fmtBrl(cliente.renda_apurada)} highlight="pip" />
            <Field label="Estado Civil" value={cliente.estado_civil} />
            <Field label="Cônjuge"      value={cliente.nome_conjuge} />
            <Field label="Regime"       value={cliente.regime_bens} />
            <Field label="Nascimento"   value={fmtDate(cliente.data_nascimento)} />
            <Field label="PEP"          value={cliente.pep}
              highlight={cliente.pep?.toUpperCase() === "SIM" ? "red" : undefined} />
          </div>
        </SectionCard>

        <SectionCard title="Contato & Localização">
          <div className="p-4 grid grid-cols-2 gap-3">
            <Field label="Telefone"  value={cliente.telefone} />
            <Field label="E-mail"    value={cliente.email} />
            <Field label="Cidade"    value={cliente.cidade} />
            <Field label="Estado"    value={cliente.estado} />
            <Field label="Canal Pref." value={at?.canal_preferencia} />
          </div>
        </SectionCard>

        <SectionCard title="Funil CGI">
          <div className="p-4 grid grid-cols-2 gap-3">
            <Field label="Fase Atual"  value={cliente.fase_atual} />
            <Field label="Responsável" value={cliente.responsavel} />
            <Field label="Atendente"   value={cliente.atendente_inicial} />
            <Field label="Score Risco" value={cliente.score_risco} highlight="pip" />
            <Field label="Última Atualiz." value={fmtDate(at?.atualizado_em)} />
            <Field label="Dias parado" value={at?.dias_sem_atualizacao != null ? `${at.dias_sem_atualizacao}d` : "—"}
              highlight={(at?.dias_sem_atualizacao ?? 0) > 7 ? "amber" : undefined} />
          </div>
        </SectionCard>
      </div>

      {/* Coluna dir */}
      <div className="flex flex-col gap-4">
        <SectionCard title="Último Atendimento"
          action={
            <a href={urlPipefy} target="_blank" rel="noreferrer"
               className="flex items-center gap-1 text-[10px] font-semibold text-pip-600 hover:underline">
              <ExternalLink size={11} /> Abrir no Pipefy
            </a>
          }
        >
          <div className="p-4 grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <Field label="Último Comentário"
                value={at?.ultimo_comentario || "Nenhum comentário registrado."} />
            </div>
            <Field label="Data Comentário"  value={fmtDate(at?.ultimo_comentario_em)} />
            <Field label="Retorno"
              value={at?.tem_retorno_agendado
                ? `Sim — ${fmtDate(at?.data_retorno_fase)}`
                : "Não agendado"} />
            <Field label="Canal"           value={at?.canal_preferencia} />
            <Field label="Tentativa"       value={at?.tentativa_contato} />
          </div>
        </SectionCard>

        <SectionCard title="Resumo Financeiro">
          <div className="p-4 grid grid-cols-2 gap-3">
            <Field label="Total Financiado"
              value={fmtBrl((contratos ?? []).reduce((s: number, c: any) => s + (c.valor_financiado ?? 0), 0))}
              highlight="pip" />
            <Field label="Contratos Ativos"
              value={`${(contratos ?? []).filter((c: any) => c.contrato_ativo).length}`} />
            <Field label="Saldo em Atraso"
              value={fmtBrl(parResumo?.saldo_em_atraso)}
              highlight={parResumo?.em_atraso > 0 ? "red" : "green"} />
            <Field label="A Vencer 30d"    value={fmtBrl(parResumo?.total_a_vencer)} highlight="amber" />
            <Field label="Total Pago"      value={fmtBrl(parResumo?.total_pago)} highlight="green" />
            <Field label="Adimplência"     value={`${parResumo?.taxa_adimplencia ?? 0}%`}
              highlight={parResumo?.taxa_adimplencia >= 100 ? "green" : "amber"} />
          </div>
        </SectionCard>

        <SectionCard title="Relacionamento Bemol">
          <div className="p-4 grid grid-cols-2 gap-3">
            <Field label="É Cliente Bemol"
              value={cliente.eh_cliente ? "Sim" : "Não"}
              highlight={cliente.eh_cliente ? "green" : undefined} />
            <Field label="Grupo de Contas" value={cliente.bsa_grupo_contas} />
            <Field label="Cliente desde"   value={fmtDate(cliente.bsa_data_criacao_cliente)} />
            <Field label="Documentos"      value={documentos?.length ?? "—"} />
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB: CONTRATOS
// ─────────────────────────────────────────────────────────────────────────────
function TabContratos({ contratos, loading }: any) {
  const [open, setOpen] = useState<string | null>(null);
  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (!contratos?.length) return <Empty message="Nenhum contrato encontrado." />;

  return (
    <div className="flex flex-col gap-3">
      {contratos.map((c: any) => (
        <div key={c.id_contrato}
          className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden border-l-4 border-l-pip-500">
          <button
            onClick={() => setOpen(open === c.id_contrato ? null : c.id_contrato)}
            className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-4">
              <span className="text-[13px] font-bold text-pip-600 font-mono shrink-0">
                {c.id_contrato}
              </span>
              <span className="text-[11px] text-gray-400">{fmtDate(c.data_contrato)}</span>
              <div className="flex gap-3 flex-1">
                <div>
                  <div className="text-[9px] text-gray-400 uppercase">Área</div>
                  <div className="text-[12px] font-semibold text-gray-900">{c.area_negocio}</div>
                </div>
                <div>
                  <div className="text-[9px] text-gray-400 uppercase">Financiado</div>
                  <div className="text-[12px] font-semibold text-gray-900">{fmtBrl(c.valor_financiado)}</div>
                </div>
                <div>
                  <div className="text-[9px] text-gray-400 uppercase">Parcelas</div>
                  <div className="text-[12px] font-semibold text-gray-900">{c.qtd_parcelas ?? "—"}</div>
                </div>
                <div>
                  <div className="text-[9px] text-gray-400 uppercase">Parcela Est.</div>
                  <div className="text-[12px] font-semibold text-gray-900">{fmtBrl(c.valor_parcela_estimado)}</div>
                </div>
              </div>
              <Badge color={c.contrato_ativo ? "green" : "gray"}>
                {c.contrato_ativo ? "Ativo" : "Encerrado"}
              </Badge>
              {open === c.id_contrato
                ? <ChevronDown size={16} className="text-gray-400" />
                : <ChevronRight size={16} className="text-gray-400" />}
            </div>
          </button>
          {open === c.id_contrato && (
            <div className="border-t border-gray-100 bg-gray-50 px-4 py-4 grid grid-cols-4 gap-4 animate-slideUp">
              <Field label="Valor Financiado" value={fmtBrl(c.valor_financiado)} highlight="pip" />
              <Field label="Valor Total"      value={fmtBrl(c.valor_total)} />
              <Field label="Entrada"          value={fmtBrl(c.valor_entrada)} />
              <Field label="Qtd. Parcelas"    value={c.qtd_parcelas} />
              <Field label="Data Contrato"    value={fmtDate(c.data_contrato)} />
              <Field label="Empresa"          value={c.empresa} />
              <Field label="Tipo"             value={c.tipo_contrato} />
              <Field label="Status"           value={c.contrato_ativo ? "Ativo" : "Encerrado"} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB: PARCELAS
// ─────────────────────────────────────────────────────────────────────────────
function TabParcelas({ resumo, detalhe, loading }: any) {
  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  const statusClass = {
    "Paga":       "bg-emerald-50 text-emerald-700 border-emerald-200",
    "Em atraso":  "bg-red-50 text-red-700 border-red-200",
    "A vencer":   "bg-amber-50 text-amber-700 border-amber-200",
  } as Record<string, string>;

  return (
    <div className="flex flex-col gap-4">
      {/* Resumo */}
      {resumo && (
        <div className="grid grid-cols-6 gap-px bg-gray-200 border border-gray-200 rounded-xl overflow-hidden">
          <KpiCard label="Total"         value={resumo.total} />
          <KpiCard label="Pagas"         value={resumo.pagas}       color="green" />
          <KpiCard label="Em Atraso"     value={resumo.em_atraso}   color={resumo.em_atraso > 0 ? "red" : "green"} />
          <KpiCard label="A Vencer"      value={resumo.a_vencer}    color="amber" />
          <KpiCard label="Max Dias Atraso" value={`${resumo.max_dias_atraso}d`} />
          <KpiCard label="Adimplência"   value={`${resumo.taxa_adimplencia}%`} color="green" />
        </div>
      )}

      {/* Detalhe */}
      <SectionCard title="Parcelas Detalhadas">
        <div className="overflow-x-auto">
          <table className="w-full text-[11px] border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                {["Contrato","Parc.","Vencimento","Pagamento","Valor","Pago","Saldo","Status","Atraso","Juros"]
                  .map(h => <th key={h} className="px-3 py-2 text-left text-[10px] font-semibold text-gray-500 whitespace-nowrap">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {(detalhe ?? []).map((p: any, i: number) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-pip-50 transition-colors">
                  <td className="px-3 py-2 font-mono text-[10px] text-gray-500">{p.id_contrato?.slice(-8)}</td>
                  <td className="px-3 py-2 font-semibold">{p.num_parcela}</td>
                  <td className="px-3 py-2">{fmtDate(p.data_vencimento)}</td>
                  <td className="px-3 py-2">{p.data_pagamento ? fmtDate(p.data_pagamento) : "—"}</td>
                  <td className="px-3 py-2 font-semibold">{fmtBrl(p.valor_parcela)}</td>
                  <td className="px-3 py-2">{fmtBrl(p.valor_pago)}</td>
                  <td className="px-3 py-2 font-semibold"
                    style={{ color: (p.saldo_parcela ?? 0) > 0.01 ? "#DC2626" : "#059669" }}>
                    {fmtBrl(p.saldo_parcela)}
                  </td>
                  <td className="px-3 py-2">
                    <span className={`px-1.5 py-0.5 rounded border text-[10px] font-semibold ${statusClass[p.status_parcela] ?? ""}`}>
                      {p.status_parcela}
                    </span>
                  </td>
                  <td className="px-3 py-2">{p.dias_atraso ? `${p.dias_atraso}d` : "—"}</td>
                  <td className="px-3 py-2">{p.juros_atraso ? fmtBrl(p.juros_atraso) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!detalhe?.length && <Empty message="Nenhuma parcela encontrada." />}
        </div>
      </SectionCard>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB: DOCUMENTOS
// ─────────────────────────────────────────────────────────────────────────────
function TabDocumentos({ docs, loading }: any) {
  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  return (
    <SectionCard title="Documentos por pessoa e operação">
      <div className="overflow-x-auto">
        <table className="w-full text-[11px] border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Operação","Pessoa","Papel","Tipo","Arquivo","Status","Ver"]
                .map(h => <th key={h} className="px-3 py-2 text-left text-[10px] font-semibold text-gray-500">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {(docs ?? []).map((d: any, i: number) => (
              <tr key={i} className="border-b border-gray-100 hover:bg-pip-50 transition-colors">
                <td className="px-3 py-2 font-mono text-[10px] text-gray-400">{d.id_card_producao?.slice(-8)}</td>
                <td className="px-3 py-2 font-semibold">{d.nome_pessoa}</td>
                <td className="px-3 py-2">
                  <Badge color="pip">{d.parte_envolvida}</Badge>
                </td>
                <td className="px-3 py-2">{d.tipo_documento}</td>
                <td className="px-3 py-2 text-gray-400 max-w-[160px] truncate">{d.nome_arquivo}</td>
                <td className="px-3 py-2">
                  <Badge color={d.status_leitura === "Sim" ? "green" : "gray"}>
                    {d.status_leitura ?? "—"}
                  </Badge>
                </td>
                <td className="px-3 py-2">
                  {d.url_documento
                    ? <a href={d.url_documento} target="_blank" rel="noreferrer"
                         className="text-pip-600 font-semibold hover:underline flex items-center gap-1">
                        <ExternalLink size={11} /> Ver
                      </a>
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!docs?.length && <Empty message="Nenhum documento encontrado." />}
      </div>
    </SectionCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB: ATENDIMENTO
// ─────────────────────────────────────────────────────────────────────────────
function TabAtendimento({ atendimentos, loading }: any) {
  const [open, setOpen] = useState<string | null>(null);

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (!atendimentos?.length) return <Empty message="Nenhum atendimento encontrado." />;

  return (
    <div className="flex flex-col gap-3">
      {atendimentos.map((a: any, i: number) => {
        const isFirst   = i === 0;
        const isOpen    = open === a.id_card_pipefy;
        const faseAtiva = faseColor(a.fase_atual, a.fase_ativa) === "green";
        const parado    = (a.dias_sem_atualizacao ?? 0) > 7;

        return (
          <div key={a.id_card_pipefy}
            className={`bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden
              border-l-4 ${isFirst ? "border-l-pip-500" : "border-l-gray-300"}`}>

            {/* ── HEADER CLICÁVEL ── */}
            <button
              onClick={() => setOpen(isOpen ? null : a.id_card_pipefy)}
              className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-4">

                {/* ID do card */}
                <span className="text-[13px] font-bold text-pip-600 font-mono shrink-0">
                  #{String(a.id_card_pipefy)}
                </span>

                {/* Data */}
                <span className="text-[11px] text-gray-400 shrink-0">
                  {fmtDate(a.criado_em)}
                </span>

                {/* Campos inline — mesmo padrão visual do TabContratos */}
                <div className="flex gap-4 flex-1 min-w-0">
                  <div>
                    <div className="text-[9px] text-gray-400 uppercase">Fase</div>
                    <div className="text-[12px] font-semibold text-gray-900 truncate max-w-[160px]">
                      {a.fase_atual}
                    </div>
                  </div>
                  <div>
                    <div className="text-[9px] text-gray-400 uppercase">Responsável</div>
                    <div className="text-[12px] font-semibold text-gray-900 truncate max-w-[160px]">
                      {a.responsavel || "—"}
                    </div>
                  </div>
                  <div>
                    <div className="text-[9px] text-gray-400 uppercase">Atualizado</div>
                    <div className={`text-[12px] font-semibold ${parado ? "text-amber-600" : "text-gray-900"}`}>
                      {fmtDate(a.atualizado_em)}
                      {parado && <span className="ml-1 text-[10px]">({a.dias_sem_atualizacao}d)</span>}
                    </div>
                  </div>
                  <div>
                    <div className="text-[9px] text-gray-400 uppercase">Campanha</div>
                    <div className="text-[12px] font-semibold text-gray-900 truncate max-w-[140px]">
                      {a.campanha || "—"}
                    </div>
                  </div>
                </div>

                {/* Badges */}
                <Badge color={faseAtiva ? "green" : "gray"}>
                  {faseAtiva ? "Ativo" : "Inativo"}
                </Badge>
                {isFirst && <Badge color="pip">Mais recente</Badge>}

                {/* Chevron */}
                {isOpen
                  ? <ChevronDown size={16} className="text-gray-400 shrink-0" />
                  : <ChevronRight size={16} className="text-gray-400 shrink-0" />}
              </div>
            </button>

            {/* ── DETALHE EXPANSÍVEL ── */}
            {isOpen && (
              <div className="border-t border-gray-100 bg-gray-50 px-4 py-4 animate-slideUp">
                <div className="grid grid-cols-4 gap-4 mb-4">
                  <Field label="Atendente Inicial" value={a.atendente_inicial} />
                  <Field label="Origem Lead"       value={a.origem_lead} />
                  <Field label="Canal Preferencial" value={a.canal_preferencia} />
                  <Field label="Tentativa Contato" value={a.tentativa_contato} />
                  <Field label="Criado em"         value={fmtDate(a.criado_em)} />
                  <Field label="Atualizado em"     value={fmtDate(a.atualizado_em)} />
                  <Field label="Retorno Agendado"
                    value={a.tem_retorno_agendado ? fmtDate(a.data_retorno_fase) : "Não"}
                    highlight={a.tem_retorno_agendado ? "pip" : undefined} />
                  <Field label="Prioridade"        value={a.prioridade_cgi} />
                </div>

                {/* Último comentário */}
                {a.ultimo_comentario && (
                  <div className="mb-4">
                    <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                      Último Comentário · {fmtDate(a.ultimo_comentario_em)}
                    </div>
                    <p className="text-[12px] text-gray-700 bg-white border border-gray-200 rounded-lg px-3 py-2.5 leading-relaxed">
                      {a.ultimo_comentario}
                    </p>
                  </div>
                )}

                {/* Botão Pipefy */}
                <a href={a.url_card_pipefy} target="_blank" rel="noreferrer"
                   className="inline-flex items-center gap-2 px-4 py-2 bg-pip-500 hover:bg-pip-600 text-white text-[12px] font-semibold rounded-xl transition-colors">
                  <ExternalLink size={13} /> Abrir card #{String(a.id_card_pipefy)} no Pipefy
                </a>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
