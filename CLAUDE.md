# CLAUDE.md — Lastro

> App local de gestão financeira e de patrimônio pessoal. Single-user, roda na máquina (localhost / Docker).
> Substitui a planilha `GestorFinanceiro2026.xlsx`: os dados vivem num banco, cotações entram ao vivo,
> e uma camada de IA categoriza lançamentos e responde como analista usando o master prompt do dono.
>
> **Nome do projeto:** Lastro. (Working name — se trocar, ajustar só aqui e nos namespaces `lastro-api` / `lastro-web`.)

---

## PROTOCOLO DE OPERAÇÃO (leia antes de qualquer tarefa)

Você é o agente que constrói este projeto. Siga isto à risca:

1. **Trabalhe por fase, em ordem.** Não comece a Fase N+1 antes da Fase N estar com seu *Definition of Done* completo e os testes passando.
2. **Respeite o MVP GATE.** Nada das Fases 4–6 é implementado antes do MVP (Fases 0–3) estar rodando. Se for pedido fora de ordem, avise e confirme antes.
3. **Pergunte antes de desviar.** Mudança de arquitetura, troca de lib, nova dependência ou novo padrão NÃO entram sem confirmação explícita. Proponha, justifique em 2 linhas, espere o ok.
4. **Teste fecha fase.** Toda fase termina com testes (pytest no back, vitest no front) verdes e lint limpo. Sem isso a fase não está fechada.
5. **Commits convencionais, pequenos.** `feat:`, `fix:`, `chore:`, `test:`, `refactor:`. Um commit = uma unidade lógica. Nada de commit gigante "fase inteira".
6. **Não invente.** Sem dado de cotação/DY/P-VP no contexto → busque na API ou peça. Nunca chute número financeiro.
7. **Escopo é sagrado.** Ideia nova boa fora do plano → adicione ao `BACKLOG` no fim deste arquivo. Não implemente no meio de uma fase.
8. **Atualize este arquivo** quando uma decisão de arquitetura mudar (com confirmação). Ele é a fonte de verdade.

---

## INVARIANTES DE DOMÍNIO (regras duras, não sugestões)

- **Dinheiro = preview editável.** Nenhum valor vindo de IA/visão grava direto no banco. Sempre passa por uma prévia que o usuário confere e edita. Parser determinístico pode gravar; IA não.
- **Cartão não é dívida.** Fatura é fluxo de caixa mensal com cashback. Sem enquadramento de "quitar dívida" / passivo em lugar nenhum da UI ou do modelo.
- **Parcelas.** Descrição no padrão `X/Y` (ex.: `Tablet 3/9`) é detectada e as parcelas futuras são projetadas nos meses corretos, ligadas por `parent_id`.
- **Total return honesto.** Rentabilidade = valorização **+** proventos recebidos. Nunca só `(atual−custo)/custo`.
- **Preço médio é derivado.** Recalculado a partir dos aportes. Nunca campo editável solto.
- **Reserva de emergência ≠ carteira.** R$ 12k em CDB/CDI são reserva, fora da carteira de risco e fora dos cálculos de alocação-alvo.
- **Camada de IA é uma só.** O mesmo serviço (a) categoriza lançamento desconhecido e (b) responde como analista (master prompt + dados do banco). Não duplicar.
- **Determinístico > IA.** Arquivo estruturado e cotação são lidos por código. IA só entra no que é genuinamente fuzzy (categoria, análise).

---

## STACK

**Backend** — Python 3.12+
- `uv` (gerenciador de pacotes e venv — **não** usar pip/poetry direto)
- FastAPI (async, com `lifespan`) · SQLModel · SQLite · Alembic (migrations)
- `httpx` async para APIs externas · `pydantic` v2 · `structlog`
- `ruff` (lint + format) · `pytest` + `pytest-asyncio`

**Frontend** — Node 20+ / `pnpm`
- Vite + React 19 + TypeScript (`strict: true`, sem `any`)
- Tailwind + shadcn/ui (tema **dark** próprio) · Framer Motion (count-up/transições)
- TanStack Query (estado de servidor) · Zod (validação de schema na borda) · Recharts (gráficos)
- `Biome` (lint + format) · `vitest` + Testing Library

**IA** — camada de provider plugável (reaproveita o padrão do Odysseus)
- Default: Ollama local. Opt-in: Claude API (ligar só pra leitura de fatura densa por print).
- Interface única `LLMProvider` com `.complete()` / `.vision()`; provider escolhido por env.

**Cotações** — brapi.dev (B3) · CoinGecko (cripto) · BCB-SGS (CDI/Selic/IPCA)
- ⚠️ brapi pede token e pode mudar limite do free tier — confirmar antes de codar a Fase 2.

**Deploy** — Docker Compose: serviços `api`, `web`, `ollama`. Imagem da `api` usa `uv`.

---

## ESTRUTURA DE PASTAS

```
lastro/
├── CLAUDE.md
├── docker-compose.yml
├── justfile                  # task runner (comandos abaixo)
├── backend/
│   ├── pyproject.toml        # uv
│   ├── alembic/
│   ├── src/lastro/
│   │   ├── main.py           # FastAPI + lifespan
│   │   ├── db.py             # engine, session
│   │   ├── models/           # SQLModel: card, transaction, position, ...
│   │   ├── schemas/          # pydantic I/O
│   │   ├── api/              # routers por domínio
│   │   ├── services/
│   │   │   ├── ingest/       # parsers determinísticos (print/texto/manual)
│   │   │   ├── quotes/       # brapi / coingecko / bcb
│   │   │   ├── llm/          # LLMProvider (ollama | claude)
│   │   │   └── analytics/    # snapshots, total return, projeção
│   │   └── core/             # config, logging
│   └── tests/
└── frontend/
    ├── package.json          # pnpm
    ├── src/
    │   ├── components/ui/     # shadcn
    │   ├── features/         # dashboard, carteira, cartoes, aportes, metas
    │   ├── lib/              # api client, query hooks, zod schemas
    │   └── App.tsx
    └── tests/
```

---

## COMMANDS (via `just`)

```
just up           # docker compose up (api + web + ollama)
just dev-api      # uv run uvicorn lastro.main:app --reload
just dev-web      # pnpm dev
just test         # pytest + vitest
just lint         # ruff check + biome check
just fmt          # ruff format + biome format
just migrate "<msg>"   # alembic revision --autogenerate -m
just upgrade      # alembic upgrade head
```
Sem `just` instalado, os comandos crus equivalentes ficam no `justfile`.

---

## MODELO DE DADOS (núcleo)

`Card` · `Transaction` (data, descrição, valor, categoria, card_id, source, installment_current/total, parent_id) · `Category` · `MerchantRule` (descrição→categoria, memória que aprende) · `Position` (ticker, tipo, qtd, preço_médio derivado, preço_atual live) · `PriceSnapshot` (foto mensal do patrimônio) · `Contribution` (aporte) · `Dividend` · `Income` · `FixedExpense` · `VariableExpense` · `Goal` · `AllocationTarget` · `AporteRule`.

---

## FASES & DEFINITION OF DONE

### Fase 0 — Skeleton
Docker Compose (api+web+ollama) sobe. FastAPI responde `/health`. SQLite + 1ª migration. Front React/shadcn no tema dark lê um endpoint.
**DoD:** `just up` funciona; front renderiza dado vindo do back; lint + 1 teste smoke verdes.

### Fase 1 — Entrada manual + regras (coração dos cartões)
Quick-entry com mini-sintaxe (`zebu 22`, `posto 35 #transporte`, `tablet 335,98 3/9`). Detecção e projeção de parcela. Entrada por print (visão → preview editável). Página Regras pré-carregada (~40 regras extraídas da planilha) que cresce sozinha.
**DoD:** lançar uma fatura inteira por print/manual com categoria e parcelas corretas; regra nova vira persistência; testes de parsing (incl. casos torto/decimal).

### Fase 2 — Carteira com preço ao vivo
Posições com preço médio derivado. Cotação live (brapi/coingecko/bcb). Snapshot mensal. Total return (preço + provento).
**DoD:** carteira atualiza sozinha; snapshot grava 1×/mês; total return bate em teste com valores conhecidos.

### Fase 3 — Dashboard  ← **MVP GATE**
Evolução do patrimônio (realizado + projeção). Comparativo carteira vs CDI/IBOV/IVVB11. Alocação por classe + real vs meta (alerta de desvio). Projeção meses/anos com aporte real (~R$3.000–3.400) + simulador de IF (taxa de retirada real = yield − inflação).
**DoD:** todos os números do dashboard derivam do banco (zero hardcode); comparativo e projeção testados.

> ⛔ **MVP GATE — usar o app de verdade por algumas semanas antes de seguir.**

#### Fase 3b — Resumo financeiro geral (extensão pós-MVP, 2026-06-27)
Inspirado no dashboard da planilha antiga (`GestorFinanceiro2026.xlsx`). O Dashboard original (Fase 3) só cobria carteira/investimentos — faltava a visão de fluxo de caixa do mês. Adiciona, no topo do Dashboard (acima da Evolução do patrimônio):
- Cards mensais: receita, despesas, total aportado, saldo do mês.
- Cards anuais: receita, despesas, saldo do ano.
- Reserva de emergência: valor guardado (editável), despesa média dos últimos 3 meses, quantos meses de reserva isso cobre.
- Tabela categoria × cartão do mês (gasto por categoria em cada cartão, como na planilha).
Endpoint novo `/dashboard/financial-summary?year=&month=`; `EmergencyReserve` ganha schema + endpoint CRUD (existia no model desde sempre, mas nunca foi exposto). Aporte sugerido (calculado pela planilha) fica de fora por ora — é território do motor de aporte (Fase 5), que já tem regras próprias.
**DoD:** mesmo padrão da Fase 3 — todos os números derivam do banco, testes cobrindo a agregação nova.

### Fase 4 — IA de categorização
LLM só pro desconhecido, salvando a decisão como `MerchantRule`. **Métrica:** % resolvido sem IA (alvo >90% em 2 meses).

### Fase 5 — Motor de aporte (executor de regras)
Encode das regras: CPTS prioridade · rotação XPML↔HGLG · BBAS3 pausada (ROE<15%) · Tesouro sem aporte · saída PSEC/BTCI/BOVA/TAEE. Input "vou aportar R$X" → distribuição que aproxima da meta sem vender. Renda passiva projetada alimenta o simulador.

### Fase 6 — Valuation + número mágico
Preço-teto: Gordon (ação) e DY-alvo (FII) → margem de segurança → veredito. Número mágico por ativo. Analista IA in-app (master prompt + dados vivos).

#### Extensões pós-roadmap (2026-06-28)
Com as 7 fases originais fechadas, seguem ajustes incrementais sem mudança de escopo:
- **Autenticação real + painel admin.** Login deixou de ser decorativo: usuário admin único, bootstrap a partir do `.env`, JWT (`bcrypt` + `pyjwt`), middleware exige token em toda rota exceto `/health` e `/auth/login`. Painel admin no front (ícone de engrenagem) permite reiniciar/encerrar os containers Docker via servidor de controle HTTP no launcher (porta 9100) — não muda a arquitetura single-user, é só a porta de entrada deixar de ser decorativa.
- **Cotação do Tesouro Direto.** Antes ficava fora do refresh automático (só renda variável tinha preço live). Passa a buscar no CSV oficial do Tesouro Transparente (`services/quotes/tesouro_direto.py`).
- **Vision de fatura via Ollama.** A extração de fatura por print, que era só Claude API opt-in, passa a funcionar com modelo local (`qwen2.5vl:3b` via Ollama) — reduz a dependência da nuvem para essa funcionalidade. Claude API continua disponível como opt-in.
- **Memória e contexto do analista.** O chat do analista (Fase 6) ganhou conversas múltiplas e nomeadas (estilo Claude Projects), com histórico persistido em banco (`Conversation`/`Message`) reenviado ao modelo a cada pergunta — antes cada pergunta era isolada. Instruções personalizadas editáveis (`AnalystInstructions`) complementam o master prompt sem substituí-lo. Painel de contexto mostra a "Memória" (somente leitura: master prompt + dados vivos da carteira que de fato entram no prompt, via `GET /analyst/memory`) e as "Instruções" (edição inline).

---

## NÃO FAZER (anti-scope-creep)

- Não implementar nada do **BACKLOG** sem promover explicitamente a uma fase.
- Não adicionar dependência nova sem confirmação.
- Não trocar SQLite por Postgres "pra escalar" — é single-user local.
- Não mandar dado financeiro pra nuvem por padrão (Claude API é opt-in e só pra visão de fatura).
- Não inventar cotação, DY, P/L, P/VP — buscar ou pedir.
- Não gravar valor de dinheiro vindo de IA sem preview humano.

## BACKLOG (v2+, fora de escopo agora)
Parser de export OFX/CSV dos bancos · swap tributário (BBDC4→ITUB4 dentro da isenção R$20k) · scraping de fundamentos · Markowitz/otimização por risco · calendário de proventos · multi-usuário · regras de transação com condições compostas (valor + conta + tag, inspirado no motor de regras do Firefly III — só vale promover se as ~40 regras atuais da planilha colidirem ou precisarem de exceção, hoje string match basta).

> **Stock split (desdobramento/grupamento)** implementado em 2026-06-27 — saiu do backlog (era inspirado no Investbrain). Modelo `StockSplit`, ajuste de quantidade/preço médio/total return via `services/portfolio/stock_split.py`, endpoint `/stock-splits`, evento no extrato da posição.
