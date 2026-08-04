export interface Cliente {
  cpf:                    string;
  nome_cliente:           string;
  fase_atual:             string;
  fase_ativa:             number;
  responsavel:            string;
  atendente_inicial:      string;
  telefone:               string;
  email:                  string;
  cidade:                 string;
  estado:                 string;
  profissao:              string;
  renda_mensal:           number | null;
  renda_apurada:          number | null;
  estado_civil:           string;
  nome_conjuge:           string | null;
  regime_bens:            string | null;
  pep:                    string;
  score_risco:            number | null;
  data_nascimento:        string | null;
  eh_cliente:             boolean;
  bsa_grupo_contas:       string | null;
  bsa_data_criacao_cliente: string | null;
  pedra:                  string | null;
  prioridade_cgi:         string | null;
}

export interface ClienteResumo {
  cpf:          string;
  nome_cliente: string;
  fase_atual:   string;
  fase_ativa:   number;
  responsavel:  string;
  telefone:     string;
}

export interface BuscaResult {
  tipo:      "cpf" | "lista";
  resultado: Cliente | ClienteResumo[];
}

export interface Contrato {
  id_contrato:            string;
  empresa:                string;
  area_negocio:           string;
  tipo_contrato:          string;
  valor_financiado:       number | null;
  valor_total:            number | null;
  valor_entrada:          number | null;
  qtd_parcelas:           number | null;
  valor_parcela_estimado: number | null;
  data_contrato:          string | null;
  contrato_ativo:         boolean;
}

export interface ParcelasResumo {
  total:             number;
  pagas:             number;
  em_atraso:         number;
  a_vencer:          number;
  vence_30d:         number;
  saldo_em_atraso:   number;
  total_a_vencer:    number;
  total_pago:        number;
  max_dias_atraso:   number;
  taxa_adimplencia:  number;
}

export interface Parcela {
  id_contrato:    string;
  num_parcela:    number;
  data_vencimento: string;
  data_pagamento: string | null;
  valor_parcela:  number;
  valor_pago:     number;
  saldo_parcela:  number;
  juros_atraso:   number | null;
  status_parcela: "Paga" | "Em atraso" | "A vencer";
  faixa_atraso:   string;
  dias_atraso:    number;
  tipo_baixa:     string | null;
}

export interface Documento {
  id_card_producao: string;
  id_card_pessoas:  string;
  nome_pessoa:      string;
  parte_envolvida:  string;
  tipo_documento:   string;
  nome_arquivo:     string;
  tipo_arquivo:     string;
  url_documento:    string;
  status_leitura:   string | null;
  finalizado:       string | null;
}

export interface Atendimento {
  id_card_pipefy:       string;
  url_card_pipefy:      string;
  fase_atual:           string;
  fase_ativa:           number;
  criador:              string;
  atendente_inicial:    string;
  responsavel:          string;
  origem_lead:          string;
  campanha:             string;
  criado_em:            string;
  atualizado_em:        string;
  dias_desde_criacao:   number;
  dias_sem_atualizacao: number;
  ultimo_comentario:    string | null;
  ultimo_comentario_em: string | null;
  dias_sem_comentario:  number;
  tentativa_contato:    string | null;
  canal_preferencia:    string | null;
  data_contato_comercial: string | null;
  data_retorno:         string | null;
  data_retorno_fase:    string | null;
  tem_retorno_agendado: boolean;
  prioridade_cgi:       string | null;
  pedra:                string | null;
  score_risco:          number | null;
}

export interface User {
  email:    string;
  name:     string;
  initials: string;
}
