# CRM CGI — Visão 360 · Bemol

App React + TypeScript + FastAPI rodando no Databricks Apps.

## Estrutura

```
crmvisao360/
├── main.py              ← FastAPI: API REST + serve dist/
├── requirements.txt     ← dependências Python
├── app.yaml             ← Databricks App config
├── package.json         ← dependências Node
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── index.html
├── logo.png             ← suba sua logo aqui na raiz
│
└── src/
    ├── main.tsx         ← entry point React
    ├── index.css        ← Tailwind + Inter
    ├── App.tsx          ← topbar + roteamento home/cliente
    │
    ├── pages/
    │   ├── HomeScreen.tsx   ← tela de busca centralizada
    │   └── ClientView.tsx   ← visão 360 com abas
    │
    ├── hooks/
    │   ├── useApi.ts        ← React Query (busca, cliente, contratos…)
    │   └── useFormatters.ts ← fmtBrl, fmtDate, fmtCpf, initials
    │
    ├── types/
    │   └── api.ts           ← interfaces TypeScript (Cliente, Contrato…)
    │
    └── components/
        └── ui.tsx           ← Badge, Field, SectionCard, KpiCard, Spinner
```

## Deploy no Databricks

### 1. Build do frontend
```bash
npm install
npm run build   # gera dist/
```

### 2. Commit dist/ + código no GitHub
```bash
git add .
git commit -m "build frontend"
git push
```

### 3. Databricks App
- **Compute → Apps → Create app → Custom**
- Deploy apontando para o branch `main`
- O `app.yaml` já configura o `uvicorn` e o `DATABRICKS_HTTP_PATH`

### 4. Logo
Coloque o arquivo `logo.png` na raiz do projeto. O favicon e a tela inicial usam ele automaticamente.

---

## Desenvolvimento local

```bash
# Terminal 1 — backend
pip install -r requirements.txt
export DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/6d304ee2888bbdbf
databricks auth login --host https://seu-workspace.azuredatabricks.net
uvicorn main:app --reload

# Terminal 2 — frontend
npm install
npm run dev   # proxy /api → localhost:8000
```

Acesse `http://localhost:3000`
