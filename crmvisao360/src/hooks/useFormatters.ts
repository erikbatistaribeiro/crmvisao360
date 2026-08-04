export function fmtBrl(v: number | null | undefined): string {
  if (v == null) return "—";
  return new Intl.NumberFormat("pt-BR", {
    style: "currency", currency: "BRL", minimumFractionDigits: 2,
  }).format(v);
}

export function fmtDate(v: string | null | undefined): string {
  if (!v) return "—";
  const s = String(v).slice(0, 10);
  if (s.length === 10) return `${s.slice(8)}/${s.slice(5, 7)}/${s.slice(0, 4)}`;
  return s;
}

export function fmtCpf(v: string | null | undefined): string {
  if (!v || v.length !== 11) return v ?? "—";
  return `${v.slice(0,3)}.${v.slice(3,6)}.${v.slice(6,9)}-${v.slice(9)}`;
}

export function initials(nome: string): string {
  const p = nome.trim().split(" ");
  return ((p[0]?.[0] ?? "") + (p[p.length - 1]?.[0] ?? "")).toUpperCase();
}

export function faseColor(fase: string, ativa: number): string {
  const ATIVAS = new Set([
    "Contato Inicial","Primeira Qualificação","Segunda Qualificação",
    "Negociação","Envio de Documentos","Análise de Cliente","Pré-Aprovado",
    "Aprovado","Formalização","Registro","Pagamento Aprovado","Operação Finalizada",
  ]);
  return ATIVAS.has(fase) || ativa === 1 ? "green" : "gray";
}

export function cleanCpf(s: string): string {
  return s.replace(/\D/g, "");
}
