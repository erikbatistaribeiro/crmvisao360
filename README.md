# CRM Visão 360 — CGI Bemol

App de CRM para o produto **CGI (Crédito com Garantia de Imóvel)** construído com [Databricks Apps](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html) + [Dash](https://dash.plotly.com/). Busca dados diretamente nas tabelas Gold do Unity Catalog sem carregamento em memória — projetado para bases com milhões de linhas.

---

## Visão geral

O app permite que o time de atendimento busque um cliente por **CPF ou nome** e acesse uma visão consolidada com:

- Dados cadastrais enriquecidos (CGI + Bemol + Pipefy)
- KPIs financeiros: total financiado, saldo em atraso, a vencer em 30 dias, adimplência
- Contratos com detalhe expansível
- Parcelas com status colorido por faixa de atraso
- Documentos com link direto para o Pipefy Storage
- Timeline de atendimento com botão **Abrir no Pipefy**

---

## Estrutura do repositório

```
crmvisao360/
│
├── app.py                          # App principal — Databricks App (Dash)
├── requirements.txt                # Dependências Python
├── app.yaml                        # Configuração do Databricks App
│
├── notebooks/
│   ├── dim_clientes_pipefy.ipynb   # Monta dim_clientes com hierarquia de fontes
│   ├── fato_contratos_cgi.ipynb    # Contratos dos clientes CGI (BSF)
│   ├── fato_parcelas_cgi.ipynb     # Parcelas com status e faixas de atraso
│   ├── fato_documentos_cgi.ipynb   # Documentos por pessoa e operação
│   └── fato_atendimentos_cgi.ipynb # Histórico de atendimento + link Pipefy
│
└── README.md
```

---

## Fontes de dados

Todas as tabelas estão no catálogo `treinamentos`, schema `erikbatista-15577-bsf`.

### Tabelas consumidas pelo app

| Tabela | Origem | Descrição |
|---|---|---|
| `dim_clientes_pipefy` | Pipefy + CGI + BSF | Dimensão de clientes deduplicada por CPF |
| `fato_contratos` | `bsf_prod.gold.contratos` | Contratos Bemol dos clientes CGI |
| `fato_parcelas` | `bsf.bsa_gold.pagamentos_parcelas_v2` | Parcelas com status de adimplência |
| `fato_documentos` | `bsf.cgi.cgi_pessoas_v2` | Documentos anexados por pessoa/operação |
| `fato_atendimentos` | `mawe.silver.campanhas_pipefy` | Cards do funil CGI com link Pipefy |

### Fontes originais (inputs dos notebooks)

| Fonte | Tabela | O que fornece |
|---|---|---|
| Pipefy — Funil CGI | `mawe.silver.campanhas_pipefy` | Leads, fases, comentários, responsáveis |
| CGI Pessoas | `bsf.cgi.cgi_pessoas_v2` | Dados cadastrais completos + documentos |
| Cadastro Bemol | `bsf.bsa_silver.clientes` | ID_CLIENTE, renda, endereço, grupo de contas |
| Contratos BSF | `bsf_prod.gold.contratos` | Histórico de contratos em todas as áreas |
| Parcelas BSF | `bsf.bsa_gold.pagamentos_parcelas_v2` | Parcelas, compensações, juros de atraso |

---

## Modelo de dados

```
dim_clientes_pipefy (cpf — PK)
    ├── fato_contratos    (cpf FK)  → contratos por área de negócio
    │       └── fato_parcelas (id_contrato FK) → adimplência por parcela
    ├── fato_documentos   (cpf FK)  → documentos por pessoa/operação
    └── fato_atendimentos (cpf FK)  → cards do funil + link Pipefy
```

### Hierarquia de enriquecimento da `dim_clientes_pipefy`

Para cada campo cadastral, a lógica de prioridade é:

```
1º bsf.cgi.cgi_pessoas_v2   → dados mais completos do produto CGI
2º bsf.bsa_silver.clientes  → cadastro geral Bemol
3º mawe.silver.campanhas_pipefy → dados do lead (fallback)
```

### Lógica de deduplicação por CPF

Um mesmo CPF pode ter múltiplos cards no funil. A regra de seleção é:

```
1º Cards em fase ativa > cards em fase não-ativa
2º Fase mais avançada no funil (ex: Aprovado > Negociação)
3º Card atualizado mais recentemente (empate)
```

**Fases ativas:** Contato Inicial → Primeira Qualificação → Segunda Qualificação → Negociação → Envio de Documentos → Análise de Cliente → Pré-Aprovado → Aprovado → Formalização → Registro → Pagamento Aprovado → Operação Finalizada

**Fases não-ativas:** Remarketing, Lead Não Qualificado, Desistente, Recusado, Negociação Fria, Pendente Análise de Crédito, Comitê de Crédito, Regularização - Conta Própria, Regularização - Imóvel Bemol, Geladeira - Regularização

---

## Notebooks — ordem de execução

Os notebooks devem ser executados na sequência abaixo, pois há dependências entre eles:

```
1. dim_clientes_pipefy.ipynb    ← base de tudo, deve rodar primeiro
2. fato_contratos_cgi.ipynb     ← depende de dim_clientes (id_cliente)
3. fato_parcelas_cgi.ipynb      ← depende de fato_contratos (id_contrato)
4. fato_documentos_cgi.ipynb    ← independente, pode rodar em paralelo com 2 e 3
5. fato_atendimentos_cgi.ipynb  ← independente, pode rodar em paralelo com 2 e 3
```

### Agendamento sugerido (Databricks Workflow)

```
Job CGI Gold  [diário — 08h]
  ├── Task 1: dim_clientes_pipefy      (depende de: campanhas_pipefy Silver)
  ├── Task 2: fato_contratos_cgi       (depende de: Task 1)
  ├── Task 3: fato_parcelas_cgi        (depende de: Task 2)
  ├── Task 4: fato_documentos_cgi      (depende de: Task 1, paralelo com Task 2)
  └── Task 5: fato_atendimentos_cgi    (depende de: Task 1, paralelo com Task 2)
```

---

## Deploy do app

### Pré-requisitos

- Databricks workspace com Unity Catalog habilitado
- SQL Warehouse ativo
- Permissão `SELECT` nas tabelas Gold para o service principal da app
- Permissão `CAN USE` no SQL Warehouse para o service principal da app

### 1. Via Databricks workspace (recomendado)

1. Carregue este repositório como um **Git folder** no seu workspace
2. Acesse **Compute → Apps → Create app**
3. Escolha **Custom** → **Next**
4. Nomeie o app (ex: `crm-cgi`) → **Create app**
5. Após o compute iniciar, clique em **Deploy**
6. Navegue até a pasta do repositório e selecione-a
7. Clique em **Deploy**

### 2. Localmente (desenvolvimento)

```bash
# Clone o repositório
git clone https://github.com/erikbatistaribeiro/crmvisao360.git
cd crmvisao360

# Crie o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Autentique com seu workspace
databricks auth login --host https://seu-workspace.azuredatabricks.net

# Configure o HTTP Path do SQL Warehouse
export DATABRICKS_HOST=https://seu-workspace.azuredatabricks.net
export DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/seu-warehouse-id

# Rode o app
python app.py
# Acesse: http://localhost:8050
```

---

## Configuração (`app.yaml`)

```yaml
command: ["python", "app.py"]

env:
  - name: DATABRICKS_HTTP_PATH
    value: "/sql/1.0/warehouses/seu-warehouse-id"  # substitua pelo seu warehouse

permissions:
  - level: "CAN_USE"
    group_name: "users"
```

---

## Dependências (`requirements.txt`)

```
databricks-sdk
databricks-sql-connector
dash
```

---

## Autenticação

O app usa `databricks.sdk.core.Config` para autenticação, seguindo o padrão oficial do [Databricks Apps Cookbook](https://apps-cookbook.dev/docs/dash/tables/tables_read):

- **No Databricks App:** autentica automaticamente via service principal da app, sem necessidade de token manual
- **Localmente:** usa OAuth U2M via `databricks auth login`

O usuário logado é identificado via HTTP headers injetados pelo Databricks App (`X-Forwarded-Email`) e exibido no avatar do topbar.

---

## Campos calculados relevantes

### `fato_parcelas`

| Campo | Lógica |
|---|---|
| `status_parcela` | `DATA_COMPENSACAO` preenchida → **Paga**; nula + vencimento ≤ hoje → **Em atraso**; nula + vencimento > hoje → **A vencer** |
| `dias_atraso` | Para pagas: dias entre vencimento e compensação. Para em atraso: dias entre vencimento e hoje |
| `faixa_atraso` | Sem atraso / 1-30d / 31-60d / 61-90d / >90d |
| `vence_30_dias` | Flag booleana — vencimento entre hoje e hoje+30 dias |
| `saldo_parcela` | `valor_parcela − valor_pago` |

### `fato_atendimentos`

| Campo | Lógica |
|---|---|
| `url_card_pipefy` | `https://app.pipefy.com/open-cards/{CODIGO}` |
| `dias_sem_atualizacao` | Dias desde `ATUALIZADO_EM` até hoje |
| `dias_sem_comentario` | Dias desde `ULTIMO_COMENTARIO_EM` até hoje |
| `data_retorno_fase` | COALESCE das datas de retorno por fase (Negociação > Envio Docs > Aprovado > 2ª Q > 1ª Q) |
| `tem_retorno_agendado` | `true` se `data_retorno_fase` > hoje |

---

## Referências

- [Databricks Apps Cookbook](https://apps-cookbook.dev/docs/intro)
- [Databricks Apps — documentação oficial](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)
- [Dash — documentação](https://dash.plotly.com/)
- [Pipefy open-cards URL](https://app.pipefy.com/open-cards/{CODIGO})
