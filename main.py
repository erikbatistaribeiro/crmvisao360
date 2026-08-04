"""
CRM CGI — FastAPI backend
Serve a API REST + o frontend React compilado (dist/)
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from databricks import sql as dbsql
from databricks.sdk.core import Config
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ── Config ────────────────────────────────────────────────────────────────────
cfg       = Config()
HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "")
DIST_DIR  = Path(__file__).parent / "dist"

# ── DB ────────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def get_conn():
    return dbsql.connect(
        server_hostname=cfg.host,
        http_path=HTTP_PATH,
        credentials_provider=lambda: cfg.authenticate,
        use_inline_params=True,   # permite %s como placeholder
    )

def run_query(sql: str, params: list[Any] | None = None) -> list[dict]:
    with get_conn().cursor() as cur:
        cur.execute(sql, params or [])
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

# ── SQL ───────────────────────────────────────────────────────────────────────
CAT = "`treinamentos`.`erikbatista-15577-bsf`"

SQL = {
    "busca_cpf": f"""
        SELECT cpf, nome_cliente, fase_atual, fase_ativa, responsavel,
               atendente_inicial, telefone, email, cidade, estado,
               profissao, renda_mensal, renda_apurada, estado_civil,
               nome_conjuge, regime_bens, pep, score_risco,
               data_nascimento, eh_cliente, bsa_grupo_contas,
               bsa_data_criacao_cliente
        FROM {CAT}.`dim_clientes_pipefy`
        WHERE cpf = %s LIMIT 1
    """,
    "busca_nome": f"""
        SELECT cpf, nome_cliente, fase_atual, fase_ativa, responsavel, telefone
        FROM {CAT}.`dim_clientes_pipefy`
        WHERE upper(nome_cliente) LIKE upper(%s)
        ORDER BY atualizado_em DESC LIMIT 10
    """,
    "contratos": f"""
        SELECT id_contrato, empresa, area_negocio, tipo_contrato,
               valor_financiado, valor_total, valor_entrada, qtd_parcelas,
               valor_parcela_estimado, data_contrato, contrato_ativo
        FROM {CAT}.`fato_contratos`
        WHERE cpf = %s ORDER BY data_contrato DESC
    """,
    "parcelas_resumo": f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN paga       THEN 1 ELSE 0 END) AS pagas,
            SUM(CASE WHEN em_atraso  THEN 1 ELSE 0 END) AS em_atraso,
            SUM(CASE WHEN a_vencer   THEN 1 ELSE 0 END) AS a_vencer,
            SUM(CASE WHEN vence_30_dias THEN 1 ELSE 0 END) AS vence_30d,
            ROUND(SUM(CASE WHEN em_atraso  THEN saldo_parcela  ELSE 0 END),2) AS saldo_em_atraso,
            ROUND(SUM(CASE WHEN a_vencer   THEN valor_parcela  ELSE 0 END),2) AS total_a_vencer,
            ROUND(SUM(valor_pago),2) AS total_pago,
            MAX(dias_atraso) AS max_dias_atraso,
            ROUND(SUM(CASE WHEN paga THEN 1.0 ELSE 0 END)/NULLIF(COUNT(*),0)*100,1) AS taxa_adimplencia
        FROM {CAT}.`fato_parcelas` WHERE cpf = %s
    """,
    "parcelas_detalhe": f"""
        SELECT id_contrato, num_parcela, data_vencimento, data_pagamento,
               valor_parcela, valor_pago, saldo_parcela, juros_atraso,
               status_parcela, faixa_atraso, dias_atraso, tipo_baixa
        FROM {CAT}.`fato_parcelas`
        WHERE cpf = %s ORDER BY data_vencimento DESC LIMIT 200
    """,
    "documentos": f"""
        SELECT id_card_producao, id_card_pessoas, nome_pessoa, parte_envolvida,
               tipo_documento, nome_arquivo, tipo_arquivo, url_documento,
               status_leitura, finalizado
        FROM {CAT}.`fato_documentos`
        WHERE cpf = %s ORDER BY id_card_producao, parte_envolvida, tipo_documento
    """,
    "atendimentos": f"""
        SELECT id_card_pipefy, url_card_pipefy, fase_atual, fase_ativa,
               criador, atendente_inicial, responsavel, origem_lead, campanha,
               criado_em, atualizado_em, dias_desde_criacao, dias_sem_atualizacao,
               ultimo_comentario, ultimo_comentario_em, dias_sem_comentario,
               tentativa_contato, canal_preferencia, data_contato_comercial,
               data_retorno, data_retorno_fase, tem_retorno_agendado,
               prioridade_cgi, pedra, score_risco
        FROM {CAT}.`fato_atendimentos`
        WHERE cpf = %s ORDER BY atualizado_em DESC
    """,
}

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="CRM CGI", docs_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth helper ───────────────────────────────────────────────────────────────
def current_user(request: Request) -> dict:
    email = request.headers.get("X-Forwarded-Email", "")
    name  = request.headers.get("X-Forwarded-Preferred-Username", email)
    parts = name.replace("@", " ").replace(".", " ").split()
    initials = "".join(p[0].upper() for p in parts[:2]) if parts else "?"
    return {"email": email, "name": name, "initials": initials}

# ── API routes ────────────────────────────────────────────────────────────────
@app.get("/api/me")
def me(request: Request):
    return current_user(request)

@app.get("/api/clientes/buscar")
def buscar_cliente(q: str):
    """Busca por CPF (11 dígitos) ou nome."""
    t = q.strip().replace(".", "").replace("-", "").replace("/", "").replace(" ", "")
    if t.isdigit() and len(t) == 11:
        rows = run_query(SQL["busca_cpf"], [t])
        if not rows:
            raise HTTPException(404, detail=f"CPF {q} não encontrado")
        return {"tipo": "cpf", "resultado": rows[0]}
    rows = run_query(SQL["busca_nome"], [f"%{q.strip()}%"])
    if not rows:
        raise HTTPException(404, detail=f"Nenhum cliente encontrado para '{q}'")
    return {"tipo": "lista", "resultado": rows}

@app.get("/api/clientes/{cpf}")
def get_cliente(cpf: str):
    rows = run_query(SQL["busca_cpf"], [cpf])
    if not rows:
        raise HTTPException(404, detail="Cliente não encontrado")
    return rows[0]

@app.get("/api/clientes/{cpf}/contratos")
def get_contratos(cpf: str):
    return run_query(SQL["contratos"], [cpf])

@app.get("/api/clientes/{cpf}/parcelas")
def get_parcelas(cpf: str, detalhe: bool = False):
    if detalhe:
        return run_query(SQL["parcelas_detalhe"], [cpf])
    rows = run_query(SQL["parcelas_resumo"], [cpf])
    return rows[0] if rows else {}

@app.get("/api/clientes/{cpf}/documentos")
def get_documentos(cpf: str):
    return run_query(SQL["documentos"], [cpf])

@app.get("/api/clientes/{cpf}/atendimentos")
def get_atendimentos(cpf: str):
    return run_query(SQL["atendimentos"], [cpf])

# ── Serve React ───────────────────────────────────────────────────────────────
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        return FileResponse(DIST_DIR / "index.html")
