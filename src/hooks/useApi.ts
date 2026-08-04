import { useQuery } from "@tanstack/react-query";
import type {
  BuscaResult, Cliente, Contrato, ParcelasResumo,
  Parcela, Documento, Atendimento, User,
} from "../types/api";

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Erro desconhecido");
  }
  return res.json();
}

export function useBusca(q: string, enabled: boolean) {
  return useQuery<BuscaResult, Error>({
    queryKey: ["busca", q],
    queryFn: () => get(`/api/clientes/buscar?q=${encodeURIComponent(q)}`),
    enabled,
    retry: false,
    staleTime: 30_000,
  });
}

export function useCliente(cpf: string | null) {
  return useQuery<Cliente, Error>({
    queryKey: ["cliente", cpf],
    queryFn: () => get(`/api/clientes/${cpf}`),
    enabled: !!cpf,
    staleTime: 60_000,
  });
}

export function useContratos(cpf: string | null) {
  return useQuery<Contrato[], Error>({
    queryKey: ["contratos", cpf],
    queryFn: () => get(`/api/clientes/${cpf}/contratos`),
    enabled: !!cpf,
    staleTime: 60_000,
  });
}

export function useParcelasResumo(cpf: string | null) {
  return useQuery<ParcelasResumo, Error>({
    queryKey: ["parcelas-resumo", cpf],
    queryFn: () => get(`/api/clientes/${cpf}/parcelas`),
    enabled: !!cpf,
    staleTime: 60_000,
  });
}

export function useParcelasDetalhe(cpf: string | null) {
  return useQuery<Parcela[], Error>({
    queryKey: ["parcelas-detalhe", cpf],
    queryFn: () => get(`/api/clientes/${cpf}/parcelas?detalhe=true`),
    enabled: !!cpf,
    staleTime: 60_000,
  });
}

export function useDocumentos(cpf: string | null) {
  return useQuery<Documento[], Error>({
    queryKey: ["documentos", cpf],
    queryFn: () => get(`/api/clientes/${cpf}/documentos`),
    enabled: !!cpf,
    staleTime: 60_000,
  });
}

export function useAtendimentos(cpf: string | null) {
  return useQuery<Atendimento[], Error>({
    queryKey: ["atendimentos", cpf],
    queryFn: () => get(`/api/clientes/${cpf}/atendimentos`),
    enabled: !!cpf,
    staleTime: 60_000,
  });
}

export function useMe() {
  return useQuery<User, Error>({
    queryKey: ["me"],
    queryFn: () => get("/api/me"),
    staleTime: Infinity,
  });
}
