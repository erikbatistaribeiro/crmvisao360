# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  CRM CGI — Databricks App                                                   ║
# ║  Baseado na documentação oficial: https://apps-cookbook.dev/docs/intro      ║
# ║  Deploy: Databricks Workspace → Compute → Apps → Create app → Deploy       ║
# ║  Local:  export DATABRICKS_HOST=https://... && python app.py                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import os
from functools import lru_cache
from flask import request as flask_request

from databricks import sql as dbsql
from databricks.sdk.core import Config

import dash
from dash import html, dcc, Input, Output, State, callback

# ── Configuração — usa databricks.sdk.core.Config ─────────────────────────────
# No Databricks App: autentica automaticamente via service principal da app
# Localmente: lê DATABRICKS_HOST + autentica via OAuth U2M (databricks auth login)
cfg = Config()

HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/seu-warehouse-id")

@lru_cache(maxsize=1)
def get_connection():
    """Conexão reutilizada via lru_cache — padrão recomendado pelo cookbook."""
    return dbsql.connect(
        server_hostname=cfg.host,
        http_path=HTTP_PATH,
        credentials_provider=lambda: cfg.authenticate,
    )

def query(sql: str, params=None):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(sql, params or [])
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

def get_current_user():
    """Lê usuário logado via HTTP headers injetados pelo Databricks App."""
    try:
        headers = flask_request.headers
        email    = headers.get("X-Forwarded-Email", "")
        username = headers.get("X-Forwarded-Preferred-Username", "")
        return email or username or "Usuário"
    except Exception:
        return "Usuário"

# ──────────────────────────────────────────────────────────────────────────────
# QUERIES — 1 cliente por vez, apenas as colunas necessárias
# ──────────────────────────────────────────────────────────────────────────────
SQL_BUSCA_CPF = """
SELECT cpf, nome_cliente, fase_atual, fase_ativa, responsavel, atendente_inicial,
       telefone, email, cidade, estado, profissao, renda_mensal, renda_apurada,
       estado_civil, nome_conjuge, regime_bens, pep, score_risco,
       data_nascimento, eh_cliente, bsa_grupo_contas, bsa_data_criacao_cliente
FROM `treinamentos`.`erikbatista-15577-bsf`.`dim_clientes_pipefy`
WHERE cpf = ?
LIMIT 1
"""

SQL_BUSCA_NOME = """
SELECT cpf, nome_cliente, fase_atual, responsavel, telefone
FROM `treinamentos`.`erikbatista-15577-bsf`.`dim_clientes_pipefy`
WHERE upper(nome_cliente) LIKE upper(?)
ORDER BY atualizado_em DESC
LIMIT 10
"""

SQL_CONTRATOS = """
SELECT id_contrato, empresa, area_negocio, tipo_contrato,
       valor_financiado, valor_total, valor_entrada, qtd_parcelas,
       valor_parcela_estimado, data_contrato, contrato_ativo,
       ano_contrato, mes_contrato
FROM `treinamentos`.`erikbatista-15577-bsf`.`fato_contratos`
WHERE cpf = ?
ORDER BY data_contrato DESC
"""

SQL_PARCELAS_RESUMO = """
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN paga THEN 1 ELSE 0 END) AS pagas,
    SUM(CASE WHEN em_atraso THEN 1 ELSE 0 END) AS em_atraso,
    SUM(CASE WHEN a_vencer THEN 1 ELSE 0 END) AS a_vencer,
    SUM(CASE WHEN vence_30_dias THEN 1 ELSE 0 END) AS vence_30d,
    ROUND(SUM(CASE WHEN em_atraso THEN saldo_parcela ELSE 0 END), 2) AS saldo_em_atraso,
    ROUND(SUM(CASE WHEN a_vencer THEN valor_parcela ELSE 0 END), 2) AS total_a_vencer,
    ROUND(SUM(valor_pago), 2) AS total_pago,
    MAX(dias_atraso) AS max_dias_atraso,
    ROUND(SUM(CASE WHEN paga THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100, 1) AS taxa_adimplencia
FROM `treinamentos`.`erikbatista-15577-bsf`.`fato_parcelas`
WHERE cpf = ?
"""

SQL_PARCELAS_DETALHE = """
SELECT id_contrato, num_parcela, data_vencimento, data_pagamento,
       valor_parcela, valor_pago, saldo_parcela, juros_atraso,
       status_parcela, faixa_atraso, dias_atraso, tipo_baixa
FROM `treinamentos`.`erikbatista-15577-bsf`.`fato_parcelas`
WHERE cpf = ?
ORDER BY data_vencimento DESC
LIMIT 200
"""

SQL_DOCUMENTOS = """
SELECT id_card_producao, id_card_pessoas, nome_pessoa, parte_envolvida,
       tipo_documento, nome_arquivo, tipo_arquivo, url_documento,
       status_leitura, finalizado
FROM `treinamentos`.`erikbatista-15577-bsf`.`fato_documentos`
WHERE cpf = ?
ORDER BY id_card_producao, parte_envolvida, tipo_documento
"""

SQL_ATENDIMENTO = """
SELECT id_card_pipefy, url_card_pipefy, fase_atual, fase_ativa,
       criador, atendente_inicial, responsavel, origem_lead, campanha,
       criado_em, atualizado_em, dias_desde_criacao, dias_sem_atualizacao,
       ultimo_comentario, ultimo_comentario_em, dias_sem_comentario,
       tentativa_contato, canal_preferencia,
       data_contato_comercial, data_retorno, data_retorno_fase,
       tem_retorno_agendado, prioridade_cgi, pedra, score_risco
FROM `treinamentos`.`erikbatista-15577-bsf`.`fato_atendimentos`
WHERE cpf = ?
ORDER BY atualizado_em DESC
"""

# ── Helpers de formatação ─────────────────────────────────────────────────────
def fmt_brl(v):
    if v is None: return "—"
    try: return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "—"

def fmt_date(v):
    if not v: return "—"
    s = str(v)[:10]
    if len(s) == 10: return s[8:]+"/"+s[5:7]+"/"+s[:4]
    return s

def fmt_cpf(v):
    if not v or len(str(v)) != 11: return v or "—"
    c = str(v)
    return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"

def iniciais(nome):
    p = (nome or "").strip().split()
    return ((p[0][0] if p else "") + (p[-1][0] if len(p) > 1 else "")).upper()

def status_color(fase):
    ativas = {"Contato Inicial","Primeira Qualificação","Segunda Qualificação",
               "Negociação","Envio de Documentos","Análise de Cliente",
               "Pré-Aprovado","Aprovado","Formalização","Registro",
               "Pagamento Aprovado","Operação Finalizada"}
    return "#059669" if fase in ativas else "#6B7280"

# ── CSS idêntico ao design original ──────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --pip:#6366F1;--pip-l:#EEF2FF;--pip-m:#C7D2FE;--pip-d:#4F46E5;--pip-dk:#3730A3;
  --g9:#111827;--g8:#1F2937;--g7:#374151;--g5:#6B7280;--g4:#9CA3AF;
  --g3:#D1D5DB;--g2:#E5E7EB;--g1:#F3F4F6;--g0:#F9FAFB;--w:#FFFFFF;
  --green:#059669;--gbg:#ECFDF5;--gbd:#A7F3D0;
  --red:#DC2626;--rbg:#FEF2F2;--rbd:#FECACA;
  --amber:#D97706;--abg:#FFFBEB;--abd:#FDE68A;
  --blue:#2563EB;--bbg:#EFF6FF;--bbd:#BFDBFE;
  --teal:#0D9488;--tbg:#F0FDFA;--tbd:#99F6E4;
  --sh:0 1px 3px rgba(0,0,0,.07),0 1px 2px rgba(0,0,0,.04);
  --shmd:0 4px 12px rgba(0,0,0,.08);
}
html,body{font-family:'Inter',-apple-system,sans-serif;font-size:13px;color:var(--g9);background:#F4F5F9;-webkit-font-smoothing:antialiased;min-height:100vh}

/* TOPBAR */
.topbar{position:sticky;top:0;z-index:200;background:var(--w);border-bottom:1px solid var(--g2);height:52px;padding:0 24px;display:flex;align-items:center;gap:12px}
.logo-mark{width:30px;height:30px;background:var(--pip);border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:15px;font-weight:800;flex-shrink:0}
.logo-text{font-size:15px;font-weight:700;color:var(--g9);letter-spacing:-.3px}
.topbar-sep{width:1px;height:22px;background:var(--g2)}
.search-wrap{display:flex;align-items:center;gap:8px;flex:1;max-width:480px}
.search-wrap input{flex:1;height:34px;border:1px solid var(--g2);border-radius:6px;padding:0 12px;font-size:12px;font-family:inherit;color:var(--g9);background:var(--g0);outline:none;transition:border .15s}
.search-wrap input:focus{border-color:var(--pip-m);background:var(--w);box-shadow:0 0 0 3px rgba(99,102,241,.08)}
.search-wrap button{height:34px;padding:0 16px;background:var(--pip);color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:600;font-family:inherit;cursor:pointer;white-space:nowrap}
.search-wrap button:hover{background:var(--pip-d)}
.topbar-right{margin-left:auto;display:flex;align-items:center;gap:8px}
.avatar{width:30px;height:30px;border-radius:50%;background:var(--pip);color:#fff;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center}

/* RESULTADOS DA BUSCA */
.search-results{background:var(--w);border:1px solid var(--g2);border-radius:8px;box-shadow:var(--shmd);margin:8px 24px;overflow:hidden}
.search-result-item{padding:10px 16px;cursor:pointer;border-bottom:1px solid var(--g1);display:flex;align-items:center;gap:12px;transition:background .1s}
.search-result-item:last-child{border-bottom:none}
.search-result-item:hover{background:var(--pip-l)}
.sri-nome{font-size:12px;font-weight:600;color:var(--g9)}
.sri-meta{font-size:11px;color:var(--g5);margin-top:1px}

/* CLIENTE HEADER */
.client-header{background:var(--w);border-bottom:1px solid var(--g2);padding:20px 24px 0;flex-shrink:0}
.client-top{display:flex;align-items:flex-start;gap:16px;margin-bottom:14px}
.client-avatar{width:52px;height:52px;border-radius:12px;background:linear-gradient(135deg,#6366F1,#8B5CF6);color:#fff;font-size:18px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.client-name{font-size:19px;font-weight:700;color:var(--g9);margin-bottom:6px;line-height:1.2}
.chips{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:5px}
.chip{font-size:11px;font-weight:500;border-radius:4px;padding:2px 8px;border:1px solid var(--g2);background:var(--g1);color:var(--g7)}
.chip.pip{background:var(--pip-l);border-color:var(--pip-m);color:var(--pip-d)}
.chip.green{background:var(--gbg);border-color:var(--gbd);color:var(--green)}
.chip.amber{background:var(--abg);border-color:var(--abd);color:var(--amber)}
.chip.red{background:var(--rbg);border-color:var(--rbd);color:var(--red)}
.chip.blue{background:var(--bbg);border-color:var(--bbd);color:var(--blue)}
.chip.teal{background:var(--tbg);border-color:var(--tbd);color:var(--teal)}
.client-meta-row{font-size:11px;color:var(--g5);display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.btn{display:inline-flex;align-items:center;gap:5px;font-family:inherit;font-size:12px;font-weight:500;border-radius:6px;padding:7px 14px;cursor:pointer;border:1px solid transparent;transition:background .12s,border-color .12s;text-decoration:none}
.btn-ghost{background:var(--w);border-color:var(--g2);color:var(--g7)}.btn-ghost:hover{background:var(--g0)}
.btn-pip{background:var(--pip);color:#fff;border-color:var(--pip)}.btn-pip:hover{background:var(--pip-d)}

/* KPI STRIP */
.kpi-row{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:var(--g2);border-top:1px solid var(--g2);margin:0 -24px}
.kpi{background:var(--w);padding:10px 16px}
.kpi-lbl{font-size:9px;font-weight:600;color:var(--g4);text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px}
.kpi-val{font-size:15px;font-weight:700;color:var(--g9)}
.kpi-sub{font-size:10px;color:var(--g5);margin-top:1px}
.kpi-val.pip{color:var(--pip-d)}.kpi-val.green{color:var(--green)}.kpi-val.amber{color:var(--amber)}.kpi-val.red{color:var(--red)}

/* TABS */
.tabs-wrap{background:var(--w);border-bottom:1px solid var(--g2);padding:10px 24px;display:flex;gap:6px;flex-wrap:wrap}
.tab-btn{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:500;color:var(--g7);padding:5px 12px;border:1.5px solid var(--g2);border-radius:20px;background:var(--w);cursor:pointer;white-space:nowrap;transition:all .12s;font-family:inherit}
.tab-btn:hover{border-color:var(--pip-m);color:var(--pip-d);background:var(--pip-l)}
.tab-btn.active{border-color:var(--pip-m);color:var(--pip-d);background:var(--pip-l);font-weight:600}

/* PANELS */
.panel{display:none;padding:20px 24px}.panel.active{display:block}
.grid-360{display:grid;grid-template-columns:320px 1fr;gap:16px;align-items:start}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}

/* SECTION CARD */
.sc{background:var(--w);border:1px solid var(--g2);border-radius:8px;box-shadow:var(--sh);overflow:hidden;margin-bottom:14px}
.sc:last-child{margin-bottom:0}
.sc-hdr{display:flex;align-items:center;justify-content:space-between;padding:9px 14px;border-bottom:1px solid var(--g1);background:var(--g0)}
.sc-title{font-size:10px;font-weight:700;color:var(--g8);text-transform:uppercase;letter-spacing:.4px}
.sc-body{padding:14px}

/* FIELD GRID */
.fg{display:grid;grid-template-columns:1fr 1fr;gap:8px 14px}
.f{display:flex;flex-direction:column;gap:1px}
.fl{font-size:9px;font-weight:600;color:var(--g4);text-transform:uppercase;letter-spacing:.4px}
.fv{font-size:11px;font-weight:500;color:var(--g9);line-height:1.4}
.fv.muted{color:var(--g5);font-weight:400}
.fv.money{font-weight:700;font-size:12px}
.fv.green{color:var(--green)}.fv.red{color:var(--red)}.fv.amber{color:var(--amber)}.fv.pip{color:var(--pip-d)}

/* TAGS */
.tag{display:inline-block;font-size:10px;font-weight:600;padding:2px 7px;border-radius:4px}
.tag.green{background:var(--gbg);color:var(--green)}.tag.amber{background:var(--abg);color:var(--amber)}
.tag.red{background:var(--rbg);color:var(--red)}.tag.blue{background:var(--bbg);color:var(--blue)}
.tag.pip{background:var(--pip-l);color:var(--pip-d)}.tag.gray{background:var(--g1);color:var(--g5)}

/* CONTRATO ROWS */
.cr{background:var(--w);border:1px solid var(--g2);border-radius:8px;box-shadow:var(--sh);overflow:hidden;cursor:pointer;margin-bottom:10px;transition:border-color .15s,box-shadow .15s}
.cr:hover{border-color:var(--pip-m);box-shadow:var(--shmd)}
.cr-hdr{display:grid;align-items:center;gap:10px;padding:12px 16px;grid-template-columns:24px 160px 120px 140px 80px 110px 1fr 90px}
.cr-hdr:hover{background:var(--g0)}
.cr-num{font-size:12px;font-weight:700;color:var(--pip-d)}
.cr-lbl{font-size:10px;color:var(--g4)}
.cr-val{font-size:12px;font-weight:600;color:var(--g9)}
.cr-detail{display:none;border-top:1px solid var(--g1);background:var(--g0);padding:16px}
.cr-detail.open{display:block}
.cr-dg{display:grid;grid-template-columns:repeat(4,1fr);gap:12px 20px}
.expand-btn{width:22px;height:22px;border-radius:4px;display:flex;align-items:center;justify-content:center;background:var(--g1);border:none;cursor:pointer;color:var(--g5);transition:all .15s;font-size:14px}
.expand-btn.open{transform:rotate(90deg);background:var(--pip-l);color:var(--pip)}
.accent-cgi{border-left:3px solid #6366F1}

/* TABLE */
.dt{width:100%;border-collapse:collapse;font-size:11px}
.dt th{background:var(--g0);padding:8px 10px;text-align:left;font-size:10px;font-weight:600;color:var(--g5);border-bottom:1px solid var(--g2);white-space:nowrap}
.dt td{padding:8px 10px;border-bottom:1px solid var(--g1);vertical-align:middle}
.dt tr:last-child td{border-bottom:none}
.dt tr:hover td{background:var(--pip-l)}

/* TIMELINE */
.tl{display:flex;flex-direction:column}
.tl-item{display:flex;gap:12px;padding:12px 0;position:relative}
.tl-item:not(:last-child)::after{content:'';position:absolute;left:14px;top:34px;width:1px;height:calc(100% - 22px);background:var(--g2)}
.tl-dot{width:28px;height:28px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;z-index:1;font-size:12px}
.tl-dot.pip{background:var(--pip-l);color:var(--pip)}
.tl-dot.green{background:var(--gbg);color:var(--green)}
.tl-dot.amber{background:var(--abg);color:var(--amber)}
.tl-body{flex:1}
.tl-title{font-size:12px;font-weight:600;color:var(--g9);margin-bottom:2px}
.tl-meta{font-size:10px;color:var(--g4);margin-bottom:3px}
.tl-text{font-size:11px;color:var(--g7);line-height:1.5;background:var(--g0);border-radius:4px;padding:6px 10px;border:1px solid var(--g2)}

/* ALERT */
.alert{border-radius:6px;padding:8px 12px;font-size:11px;font-weight:500;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.alert.amber{background:var(--abg);border:1px solid var(--abd);color:var(--amber)}
.alert.red{background:var(--rbg);border:1px solid var(--rbd);color:var(--red)}

/* DOCS TABLE link */
.doc-link{color:var(--pip-d);text-decoration:none;font-size:11px;font-weight:500}
.doc-link:hover{text-decoration:underline}

/* EMPTY STATE */
.empty{text-align:center;padding:40px 20px;color:var(--g4);font-size:12px}
"""

# ── Layout do App ─────────────────────────────────────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.index_string = f"""
<!DOCTYPE html><html lang="pt-BR">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>CRM CGI — Bemol</title>
<style>{CSS}</style>
{{%metas%}}{{%favicon%}}{{%css%}}</head>
<body>{{%app_entry%}}{{%config%}}{{%scripts%}}{{%renderer%}}</body></html>
"""

app.layout = html.Div([
    # TOPBAR
    html.Header([
        html.Div("B", className="logo-mark"),
        html.Span("CRM CGI", className="logo-text"),
        html.Div(className="topbar-sep"),
        html.Div([
            dcc.Input(id="search-input", type="text",
                      placeholder="Buscar por CPF ou nome...",
                      debounce=False,
                      style={"width": "100%"}),
            html.Button("Buscar", id="search-btn"),
        ], className="search-wrap"),
        html.Div([
        html.Div(id="user-avatar", className="avatar", children="?"),
    ], className="topbar-right"),
    # Location trigger para ler headers (só funciona no Databricks App)
    dcc.Location(id="url", refresh=False),
    ], className="topbar"),

    # RESULTADOS DA BUSCA
    html.Div(id="search-results", style={"display": "none"}),

    # CONTEÚDO DO CLIENTE
    html.Div(id="client-content"),

    # Stores
    dcc.Store(id="cpf-store"),
    dcc.Store(id="tab-store", data="p-360"),
])

# ── Callback: Avatar do usuário logado ────────────────────────────────────────
@callback(
    Output("user-avatar", "children"),
    Input("url", "pathname"),
)
def update_avatar(_):
    user = get_current_user()
    # Pega iniciais: "erik.batista@bemol.com.br" → "EB"
    partes = user.replace("@", " ").replace(".", " ").split()
    iniciais_user = "".join(p[0].upper() for p in partes[:2]) if partes else "?"
    return iniciais_user

# ── Callback: Busca ───────────────────────────────────────────────────────────
@callback(
    Output("search-results", "children"),
    Output("search-results", "style"),
    Input("search-btn", "n_clicks"),
    Input("search-input", "n_submit"),
    State("search-input", "value"),
    prevent_initial_call=True,
)
def buscar(_, __, termo):
    if not termo or not termo.strip():
        return [], {"display": "none"}
    t = termo.strip().replace(".", "").replace("-", "").replace("/", "")
    if t.isdigit() and len(t) == 11:
        rows = query(SQL_BUSCA_CPF, [t])
        if rows:
            r = rows[0]
            return build_client_content(r, t), {"display": "none"}
        return [html.Div("CPF não encontrado.", className="empty")], {"display": "block"}
    rows = query(SQL_BUSCA_NOME, ["%" + termo.strip() + "%"])
    if not rows:
        return [html.Div("Nenhum cliente encontrado.", className="empty")], {"display": "block"}
    items = [
        html.Div([
            html.Div(r.get("nome_cliente", ""), className="sri-nome"),
            html.Div(
                f"CPF: {fmt_cpf(r.get('cpf',''))} · {r.get('fase_atual','')} · {r.get('responsavel','')}",
                className="sri-meta"
            ),
        ], className="search-result-item",
           id={"type": "sri", "cpf": r.get("cpf", "")})
        for r in rows
    ]
    return items, {"display": "block"}

# ── Callback: Clique em resultado ─────────────────────────────────────────────
@callback(
    Output("search-results", "style", allow_duplicate=True),
    Output("client-content", "children", allow_duplicate=True),
    Input({"type": "sri", "cpf": dash.ALL}, "n_clicks"),
    State({"type": "sri", "cpf": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def selecionar_cliente(clicks, ids):
    ctx = dash.callback_context
    if not ctx.triggered or all(c is None for c in clicks):
        raise dash.exceptions.PreventUpdate
    idx = next(i for i, c in enumerate(clicks) if c)
    cpf = ids[idx]["cpf"]
    rows = query(SQL_BUSCA_CPF, [cpf])
    if not rows:
        raise dash.exceptions.PreventUpdate
    content = build_client_content(rows[0], cpf)
    return {"display": "none"}, content

# ── Callback: Trocar aba ──────────────────────────────────────────────────────
@callback(
    Output({"type": "panel", "id": dash.ALL}, "className"),
    Output({"type": "tab", "id": dash.ALL}, "className"),
    Input({"type": "tab", "id": dash.ALL}, "n_clicks"),
    State({"type": "tab", "id": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def trocar_aba(clicks, ids):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop = ctx.triggered[0]["prop_id"]
    import json
    aba_id = json.loads(prop.split(".")[0])["id"]
    panel_classes = ["panel active" if i["id"] == aba_id else "panel" for i in ids]
    tab_classes = ["tab-btn active" if i["id"] == aba_id else "tab-btn" for i in ids]
    return panel_classes, tab_classes

# ── Callback: Expandir/colapsar contrato ─────────────────────────────────────
@callback(
    Output({"type": "cr-detail", "cid": dash.ALL}, "className"),
    Output({"type": "cr-btn", "cid": dash.ALL}, "className"),
    Input({"type": "cr-hdr", "cid": dash.ALL}, "n_clicks"),
    State({"type": "cr-detail", "cid": dash.ALL}, "id"),
    State({"type": "cr-detail", "cid": dash.ALL}, "className"),
    prevent_initial_call=True,
)
def toggle_contrato(clicks, ids, classes):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop = ctx.triggered[0]["prop_id"]
    import json
    cid = json.loads(prop.split(".")[0])["cid"]
    new_cls = []
    new_btn = []
    for i, c in zip(ids, classes):
        if i["cid"] == cid:
            is_open = "open" in (c or "")
            new_cls.append("cr-detail" if is_open else "cr-detail open")
            new_btn.append("expand-btn" if is_open else "expand-btn open")
        else:
            new_cls.append(c or "cr-detail")
            new_btn.append("expand-btn")
    return new_cls, new_btn

# ── Build: conteúdo completo do cliente ───────────────────────────────────────
def build_client_content(c, cpf):
    contratos    = query(SQL_CONTRATOS, [cpf])
    parc_res     = query(SQL_PARCELAS_RESUMO, [cpf])
    parc_det     = query(SQL_PARCELAS_DETALHE, [cpf])
    docs         = query(SQL_DOCUMENTOS, [cpf])
    atendimentos = query(SQL_ATENDIMENTO, [cpf])

    p  = parc_res[0] if parc_res else {}
    at = atendimentos[0] if atendimentos else {}

    em_atraso    = int(p.get("em_atraso", 0) or 0) > 0
    card_parado  = int(at.get("dias_sem_atualizacao", 0) or 0) > 7
    fase_cor     = status_color(c.get("fase_atual", ""))
    url_pipefy   = at.get("url_card_pipefy", "#")

    abas = ["p-360", "p-cgi", "p-parcelas", "p-docs", "p-atend"]

    return html.Div([

        # ── HEADER DO CLIENTE ──────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div(iniciais(c.get("nome_cliente", "")), className="client-avatar"),
                html.Div([
                    html.Div(c.get("nome_cliente", "").upper(), className="client-name"),
                    html.Div([
                        html.Span(f"CPF: {fmt_cpf(cpf)}", className="chip pip"),
                        html.Span(c.get("fase_atual", ""), className="chip",
                                  style={"background": fase_cor + "15",
                                         "borderColor": fase_cor + "50",
                                         "color": fase_cor}),
                        html.Span("Cliente Bemol" if c.get("eh_cliente") else "Prospect",
                                  className="chip blue" if c.get("eh_cliente") else "chip"),
                        *([html.Span("PEP", className="chip red")]
                          if str(c.get("pep", "")).upper() in ("SIM", "S", "TRUE", "1") else []),
                    ], className="chips"),
                    html.Div([
                        f"📞 {c.get('telefone','—')}  ·  ✉ {c.get('email','—')}  ·  {c.get('cidade','')}",
                    ], className="client-meta-row"),
                ], style={"flex": 1}),
                html.A("↗ Abrir no Pipefy", href=url_pipefy, target="_blank",
                       className="btn btn-pip", style={"marginLeft": "auto", "flexShrink": 0}),
            ], className="client-top"),

            # KPI STRIP
            html.Div([
                html.Div([html.Div("Financiado", className="kpi-lbl"),
                          html.Div(fmt_brl(sum(r.get("valor_financiado", 0) or 0 for r in contratos)),
                                   className="kpi-val pip"),
                          html.Div(f"{len(contratos)} contrato(s)", className="kpi-sub")]),
                html.Div([html.Div("Em Atraso", className="kpi-lbl"),
                          html.Div(fmt_brl(p.get("saldo_em_atraso", 0)),
                                   className="kpi-val red" if em_atraso else "kpi-val green"),
                          html.Div(f"{p.get('em_atraso', 0)} parcela(s)", className="kpi-sub")]),
                html.Div([html.Div("A Vencer 30d", className="kpi-lbl"),
                          html.Div(fmt_brl(p.get("total_a_vencer", 0)), className="kpi-val amber"),
                          html.Div(f"{p.get('vence_30d', 0)} parcela(s)", className="kpi-sub")]),
                html.Div([html.Div("Total Pago", className="kpi-lbl"),
                          html.Div(fmt_brl(p.get("total_pago", 0)), className="kpi-val green"),
                          html.Div(f"Adimpl.: {p.get('taxa_adimplencia', 0):.1f}%", className="kpi-sub")]),
                html.Div([html.Div("Score Risco", className="kpi-lbl"),
                          html.Div(str(c.get("score_risco") or "—"), className="kpi-val pip"),
                          html.Div(f"Renda: {fmt_brl(c.get('renda_mensal'))}", className="kpi-sub")]),
                html.Div([html.Div("Documentos", className="kpi-lbl"),
                          html.Div(str(len(docs)), className="kpi-val"),
                          html.Div(f"Pessoas: {len(set(d.get('id_card_pessoas','') for d in docs))}",
                                   className="kpi-sub")]),
            ], className="kpi-row"),

        ], className="client-header"),

        # ── ABAS ──────────────────────────────────────────────────────────
        html.Div([
            html.Button("Visão 360°",    id={"type":"tab","id":"p-360"},   n_clicks=0, className="tab-btn active"),
            html.Button(f"CGI ({len(contratos)})", id={"type":"tab","id":"p-cgi"}, n_clicks=0, className="tab-btn"),
            html.Button(f"Parcelas ({len(parc_det)})", id={"type":"tab","id":"p-parcelas"}, n_clicks=0, className="tab-btn"),
            html.Button(f"Documentos ({len(docs)})", id={"type":"tab","id":"p-docs"}, n_clicks=0, className="tab-btn"),
            html.Button(f"Atendimento ({len(atendimentos)})", id={"type":"tab","id":"p-atend"}, n_clicks=0, className="tab-btn"),
        ], className="tabs-wrap"),

        # ── PAINEL 1: VISÃO 360 ───────────────────────────────────────────
        html.Div([
            html.Div([
                # Coluna esquerda
                html.Div([
                    build_card("Dados Pessoais", html.Div([
                        html.Div([
                            field("Nome", c.get("nome_cliente","")),
                            field("CPF", fmt_cpf(cpf)),
                            field("Profissão", c.get("profissao","—")),
                            field("Renda Mensal", fmt_brl(c.get("renda_mensal")), "money"),
                            field("Renda Apurada", fmt_brl(c.get("renda_apurada")), "money"),
                            field("Estado Civil", c.get("estado_civil","—")),
                            field("Cônjuge", c.get("nome_conjuge","—")),
                            field("Regime de Bens", c.get("regime_bens","—")),
                            field("PEP", c.get("pep","Não")),
                            field("Nascimento", fmt_date(c.get("data_nascimento"))),
                        ], className="fg"),
                    ], className="sc-body")),
                    build_card("Contato & Endereço", html.Div([
                        html.Div([
                            field("Telefone", c.get("telefone","—")),
                            field("E-mail", c.get("email","—")),
                            field("Cidade / Estado", f"{c.get('cidade','—')} / {c.get('estado','—')}"),
                            field("Canal Pref.", at.get("canal_preferencia","—")),
                        ], className="fg"),
                    ], className="sc-body")),
                    build_card("Funil CGI", html.Div([
                        html.Div([
                            field("Fase Atual", c.get("fase_atual","—")),
                            field("Responsável", c.get("responsavel","—")),
                            field("Atendente Inicial", c.get("atendente_inicial","—")),
                            field("Score Risco", str(c.get("score_risco") or "—")),
                            field("Última Atualização", fmt_date(at.get("atualizado_em"))),
                            field("Dias sem Atualiz.", str(at.get("dias_sem_atualizacao","—"))),
                        ], className="fg"),
                    ], className="sc-body")),
                ]),
                # Coluna direita
                html.Div([
                    # Alertas
                    *([html.Div(["⚠  ", f"{p.get('em_atraso',0)} parcela(s) em atraso — {fmt_brl(p.get('saldo_em_atraso',0))}"], className="alert red")] if em_atraso else []),
                    *([html.Div(["⚠  ", f"Card sem atualização há {at.get('dias_sem_atualizacao',0)} dias"], className="alert amber")] if card_parado else []),

                    build_card("Último Atendimento", html.Div([
                        html.Div([
                            field("Último Comentário", at.get("ultimo_comentario","—")),
                            field("Data Comentário", fmt_date(at.get("ultimo_comentario_em"))),
                            field("Retorno Agendado",
                                  f"Sim — {fmt_date(at.get('data_retorno_fase'))}"
                                  if at.get("tem_retorno_agendado") else "Não"),
                            field("Tentativa Contato", at.get("tentativa_contato","—")),
                        ], className="fg"),
                        html.Div([
                            html.A("↗ Abrir card no Pipefy", href=url_pipefy, target="_blank",
                                   className="btn btn-pip",
                                   style={"marginTop":"12px","display":"inline-flex"}),
                        ])
                    ], className="sc-body")),

                    build_card("Resumo Financeiro", html.Div([
                        html.Div([
                            field("Total Financiado",
                                  fmt_brl(sum(r.get("valor_financiado",0) or 0 for r in contratos)), "money pip"),
                            field("Contratos Ativos", str(sum(1 for r in contratos if r.get("contrato_ativo")))),
                            field("Saldo em Atraso", fmt_brl(p.get("saldo_em_atraso",0)),
                                  "money red" if em_atraso else "money green"),
                            field("A Vencer 30d", fmt_brl(p.get("total_a_vencer",0)), "money amber"),
                            field("Total Pago", fmt_brl(p.get("total_pago",0)), "money green"),
                            field("Adimplência", f"{p.get('taxa_adimplencia',0):.1f}%"),
                        ], className="fg"),
                    ], className="sc-body")),

                    build_card("Relacionamento Bemol", html.Div([
                        html.Div([
                            field("É Cliente Bemol",
                                  "Sim" if c.get("eh_cliente") else "Não"),
                            field("Grupo de Contas", c.get("bsa_grupo_contas","—")),
                            field("Cliente desde", fmt_date(c.get("bsa_data_criacao_cliente"))),
                            field("Documentos", str(len(docs))),
                        ], className="fg"),
                    ], className="sc-body")),
                ]),
            ], className="grid-360"),
        ], id={"type":"panel","id":"p-360"}, className="panel active"),

        # ── PAINEL 2: CONTRATOS CGI ───────────────────────────────────────
        html.Div([
            html.Div([
                html.Span(f"Contratos CGI — {len(contratos)} contrato(s)",
                          style={"fontSize":"15px","fontWeight":"700"}),
                html.Span(f"Total financiado: {fmt_brl(sum(r.get('valor_financiado',0) or 0 for r in contratos))}",
                          style={"fontSize":"12px","color":"var(--g5)","marginLeft":"8px"}),
            ], style={"marginBottom":"16px","display":"flex","alignItems":"center","gap":"8px"}),
            *build_contratos(contratos),
        ], id={"type":"panel","id":"p-cgi"}, className="panel"),

        # ── PAINEL 3: PARCELAS ────────────────────────────────────────────
        html.Div([
            # Resumo de parcelas
            html.Div([
                html.Div([html.Div("Total", className="kpi-lbl"), html.Div(str(p.get("total",0)), className="kpi-val")]),
                html.Div([html.Div("Pagas", className="kpi-lbl"), html.Div(str(p.get("pagas",0)), className="kpi-val green")]),
                html.Div([html.Div("Em Atraso", className="kpi-lbl"), html.Div(str(p.get("em_atraso",0)), className="kpi-val red" if em_atraso else "kpi-val green")]),
                html.Div([html.Div("A Vencer", className="kpi-lbl"), html.Div(str(p.get("a_vencer",0)), className="kpi-val amber")]),
                html.Div([html.Div("Max Dias Atraso", className="kpi-lbl"), html.Div(str(p.get("max_dias_atraso",0)), className="kpi-val")]),
                html.Div([html.Div("Adimplência", className="kpi-lbl"), html.Div(f"{p.get('taxa_adimplencia',0):.1f}%", className="kpi-val green")]),
            ], style={"display":"grid","gridTemplateColumns":"repeat(6,1fr)","gap":"1px",
                      "background":"var(--g2)","border":"1px solid var(--g2)","borderRadius":"8px",
                      "overflow":"hidden","marginBottom":"16px"},
               className=""),
            build_card("Detalhe das Parcelas", html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(h) for h in ["Contrato","Parc.","Vencimento","Pagamento",
                                             "Valor","Pago","Saldo","Status","Atraso","Juros"]
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(r.get("id_contrato","")[:15], style={"fontFamily":"monospace","fontSize":"10px"}),
                            html.Td(str(r.get("num_parcela",""))),
                            html.Td(fmt_date(r.get("data_vencimento"))),
                            html.Td(fmt_date(r.get("data_pagamento")) if r.get("data_pagamento") else "—"),
                            html.Td(fmt_brl(r.get("valor_parcela")), style={"fontWeight":"600"}),
                            html.Td(fmt_brl(r.get("valor_pago"))),
                            html.Td(fmt_brl(r.get("saldo_parcela")),
                                    style={"color":"var(--red)" if (r.get("saldo_parcela") or 0) > 0.01 else "var(--green)","fontWeight":"600"}),
                            html.Td(html.Span(r.get("status_parcela",""),
                                             className=f"tag {'green' if r.get('status_parcela')=='Paga' else ('red' if r.get('status_parcela')=='Em atraso' else 'amber')}")),
                            html.Td(f"{r.get('dias_atraso',0)} d" if r.get("dias_atraso") else "—"),
                            html.Td(fmt_brl(r.get("juros_atraso")) if r.get("juros_atraso") else "—"),
                        ]) for r in parc_det
                    ]),
                ], className="dt"),
            ], style={"padding":"0","overflowX":"auto"})),
        ], id={"type":"panel","id":"p-parcelas"}, className="panel"),

        # ── PAINEL 4: DOCUMENTOS ──────────────────────────────────────────
        html.Div([
            build_card("Documentos por pessoa e operação", html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(h) for h in ["Operação","Pessoa","Papel","Tipo","Arquivo","Status","Ver"]
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(str(d.get("id_card_producao",""))[:12], style={"fontSize":"10px","fontFamily":"monospace"}),
                            html.Td(d.get("nome_pessoa","—"), style={"fontWeight":"500"}),
                            html.Td(html.Span(d.get("parte_envolvida",""), className="tag pip",
                                             style={"fontSize":"9px"})),
                            html.Td(d.get("tipo_documento","")),
                            html.Td(d.get("nome_arquivo","")[:30], style={"fontSize":"10px","color":"var(--g5)"}),
                            html.Td(html.Span(d.get("status_leitura","—"),
                                             className=f"tag {'green' if d.get('status_leitura')=='Sim' else 'gray'}")),
                            html.Td(html.A("↗ Ver", href=d.get("url_documento","#"), target="_blank",
                                          className="doc-link") if d.get("url_documento") else "—"),
                        ]) for d in docs
                    ]),
                ], className="dt"),
            ], style={"padding":"0","overflowX":"auto"})),
        ], id={"type":"panel","id":"p-docs"}, className="panel"),

        # ── PAINEL 5: ATENDIMENTO ─────────────────────────────────────────
        html.Div([
            html.Div(className="grid-2", children=[
                html.Div([
                    build_card("Timeline de Atendimentos", html.Div([
                        html.Div([
                            html.Div([
                                html.Div("💬", className=f"tl-dot {'pip' if i==0 else 'green'}"),
                                html.Div([
                                    html.Div([
                                        html.Span(f"Card #{at_r.get('id_card_pipefy','')[:8]}",
                                                  style={"fontWeight":"600","fontSize":"12px"}),
                                        html.Span(at_r.get("fase_atual",""), className="chip",
                                                  style={"marginLeft":"6px","fontSize":"9px"}),
                                    ], className="tl-title"),
                                    html.Div(
                                        f"{fmt_date(at_r.get('criado_em'))} · {at_r.get('responsavel','—')}",
                                        className="tl-meta"
                                    ),
                                    html.Div(at_r.get("ultimo_comentario","Sem comentário."),
                                             className="tl-text"),
                                    html.A("↗ Abrir no Pipefy",
                                           href=at_r.get("url_card_pipefy","#"), target="_blank",
                                           className="doc-link",
                                           style={"marginTop":"6px","display":"inline-block"}),
                                ], className="tl-body"),
                            ], className="tl-item")
                            for i, at_r in enumerate(atendimentos)
                        ], className="tl"),
                    ], className="sc-body")),
                ]),
                html.Div([
                    build_card("Dados do Atendimento Atual", html.Div([
                        html.Div([
                            field("Fase Atual", at.get("fase_atual","—")),
                            field("Responsável", at.get("responsavel","—")),
                            field("Criado em", fmt_date(at.get("criado_em"))),
                            field("Atualizado em", fmt_date(at.get("atualizado_em"))),
                            field("Dias sem atualiz.", str(at.get("dias_sem_atualizacao","—"))),
                            field("Retorno agendado",
                                  fmt_date(at.get("data_retorno_fase")) if at.get("tem_retorno_agendado") else "Não"),
                            field("Canal Preferencial", at.get("canal_preferencia","—")),
                            field("Tentativa Contato", at.get("tentativa_contato","—")),
                            field("Origem Lead", at.get("origem_lead","—")),
                            field("Campanha", at.get("campanha","—")),
                        ], className="fg"),
                        html.A("↗ Abrir card no Pipefy", href=url_pipefy, target="_blank",
                               className="btn btn-pip",
                               style={"marginTop":"14px","display":"inline-flex"}),
                    ], className="sc-body")),
                ]),
            ]),
        ], id={"type":"panel","id":"p-atend"}, className="panel"),

    ])


def build_card(title, content):
    return html.Div([
        html.Div(html.Span(title, className="sc-title"), className="sc-hdr"),
        content,
    ], className="sc")


def field(label, value, extra_class=""):
    return html.Div([
        html.Span(label, className="fl"),
        html.Span(str(value) if value is not None else "—",
                  className=f"fv {extra_class}"),
    ], className="f")


def build_contratos(contratos):
    if not contratos:
        return [html.Div("Nenhum contrato encontrado.", className="empty")]
    rows = []
    for i, r in enumerate(contratos):
        cid = f"c{i}"
        rows.append(html.Div([
            html.Div([
                html.Button("›", id={"type":"cr-btn","cid":cid}, className="expand-btn",
                            style={"background":"none","border":"none","fontSize":"16px","cursor":"pointer","color":"var(--g5)"}),
                html.Div([
                    html.Div(r.get("id_contrato",""), className="cr-num"),
                    html.Div(fmt_date(r.get("data_contrato")), style={"fontSize":"10px","color":"var(--g4)"}),
                ]),
                html.Div([html.Div("Área", className="cr-lbl"), html.Div(r.get("area_negocio",""), className="cr-val")]),
                html.Div([html.Div("Financiado", className="cr-lbl"), html.Div(fmt_brl(r.get("valor_financiado")), className="cr-val")]),
                html.Div([html.Div("Parcelas", className="cr-lbl"), html.Div(str(r.get("qtd_parcelas","")), className="cr-val")]),
                html.Div([html.Div("Parcela Est.", className="cr-lbl"), html.Div(fmt_brl(r.get("valor_parcela_estimado")), className="cr-val")]),
                html.Span("Ativo" if r.get("contrato_ativo") else "Encerrado",
                          className="tag green" if r.get("contrato_ativo") else "tag gray"),
            ], id={"type":"cr-hdr","cid":cid}, className="cr-hdr", n_clicks=0),
            html.Div([
                html.Div([
                    field("Valor Financiado", fmt_brl(r.get("valor_financiado"))),
                    field("Valor Total", fmt_brl(r.get("valor_total"))),
                    field("Entrada", fmt_brl(r.get("valor_entrada"))),
                    field("Qtd. Parcelas", str(r.get("qtd_parcelas","—"))),
                    field("Data Contrato", fmt_date(r.get("data_contrato"))),
                    field("Empresa", r.get("empresa","—")),
                    field("Tipo", r.get("tipo_contrato","—")),
                    field("Status", "Ativo" if r.get("contrato_ativo") else "Encerrado"),
                ], className="cr-dg"),
            ], id={"type":"cr-detail","cid":cid}, className="cr-detail"),
        ], className="cr accent-cgi"))
    return rows


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
