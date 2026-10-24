# Roadmap — Onboarding Agent (POC)

Objetivo: construir do zero um agent pequeno com a stack que o mercado pede
(**agent + LangChain/LangGraph + RAG + evals + observabilidade + deploy**),
encaixando a teoria da trilha na prática.

Desenho: [`ARQUITETURA.md`](ARQUITETURA.md) · Decisões: [`docs/decisoes.md`](docs/decisoes.md)

Legenda: `[x]` feito · `[ ]` pendente

---

## Regras do projeto

1. **Toda fase termina com algo rodando.** Nada de passar 3 fases sem executar código.
2. **A IA escreve, você lê e questiona.** O código vem pronto e comentado. Você lê
   tudo, pergunta o que não entendeu e precisa saber explicar cada parte (Modo 2 da
   trilha). Decidido em 2026-10-22: escrever tudo do zero tomava tempo demais.
3. **Teoria entra quando precisa.** Cada fase aponta qual pasta da trilha ler
   *naquele momento*, não antes.
4. **Toda decisão vai pro `docs/decisoes.md`**, com as opções, o que foi escolhido e o porquê.
   Isso vira resposta de entrevista.
5. **Fechou a fase → explicar em voz alta** o que foi feito e por quê (de preferência em inglês).

---

## Fase 0 — Setup, Docker e primeira rota

Teoria de apoio: `p0-software-engineering/fastapi/` e `p1-production/docker-cicd/`

- [x] Decisões D1, D3, D4 (Claude, pgvector em Docker, Langfuse Cloud)
- [x] Decisão D2 (uv)
- [x] `git init`, `.gitignore`, `pyproject.toml` (via `uv init`)
- [x] `app/api.py` com `GET /health` → `{"status": "ok"}`
- [x] `app/config.py` lendo `.env` (pydantic-settings) + `.env.example`
- [x] `Dockerfile` da API + `docker-compose.yml` com `api` + `db` (imagem `pgvector/pgvector`)
- [x] Hot reload no container (volume do código + `uvicorn --reload`)
- [x] `/health` também checa se o banco responde
- [x] Primeiro teste com pytest + `TestClient` para `/health`

**Pronto quando:** `docker compose up` sobe os dois containers, `/health` responde
(com o banco ok) e o `pytest` passa.

## Fase 1 — Chamar o LLM (prompt engineering na prática)

Teoria de apoio: `p0-llm-engineering/` (prompt engineering, que é onde você está no rodízio)

- [x] `app/llm.py`: criar o modelo via LangChain, com o provider configurável por env
- [x] `POST /chat` recebe `{message}` e devolve `{answer}`, sem tools ainda
- [x] System prompt em `app/agent/prompts.py`: papel, tom, "se não souber, diga que não sabe"
- [x] Testar 3 versões do prompt com as mesmas 5 perguntas e anotar a diferença
- [x] Teste da rota com o LLM **mockado** (teste não pode depender de API externa)
- [x] Contagem de tokens: `usage` na resposta do `/chat` + `POST /chat/count-tokens` (conta antes, via API da Anthropic)

**Pronto quando:** `/chat` responde e você consegue explicar o papel de cada mensagem (system/user).

## Fase 2 — Observabilidade desde cedo

Teoria de apoio: `p1-production/observabilidade/`

- [x] Criar conta/projeto no Langfuse Cloud e pôr as chaves no `.env`
- [x] Integrar o Langfuse (callback handler do LangChain)
- [ ] Ver no painel: prompt, resposta, tokens, custo, latência
- [x] Adicionar `session_id`/`user_id` nos traces

**Pronto quando:** você abre um trace e explica cada campo. Entra cedo porque
daqui pra frente todo debug passa por ele.

## Fase 3 — RAG (tool `search_docs`)

Teoria de apoio: `p0-retrieval-data/rag/` (e fechar o `mini_rag.py`, que é a mesma ideia "na mão")

- [ ] Criar 5–8 docs fictícios em `data/docs/` (README do projeto, roadmap, deploy, contatos, padrões de código)
- [ ] Decidir o modelo de embedding (D5: API paga vs modelo local) e registrar
- [ ] `ingest.py`: carregar `.md` → dividir em chunks → embeddings → pgvector
- [ ] Abrir o Postgres e olhar a tabela de vetores com SQL (entender o que foi gravado)
- [ ] `retriever.py`: busca top-k e devolve texto + fonte
- [ ] Testar o retriever **sozinho**, sem LLM: as perguntas trazem os chunks certos?
- [ ] Ligar no `/chat`: contexto recuperado entra no prompt, a resposta cita a fonte
- [ ] Orçamento de tokens do contexto: contar os chunks antes de montar o prompt (`get_num_tokens_from_messages`, API `count_tokens`, gratuita) e cortar se passar do limite definido

**Pronto quando:** a pergunta "como faço deploy?" traz o chunk do doc de deploy e a resposta cita o arquivo.

## Fase 4 — Evals v1

Teoria de apoio: `p0-retrieval-data/evals/` (e fechar o `eval_mini.py`)

- [ ] `evals/dataset.jsonl` com 15–20 perguntas: pergunta, resposta esperada e doc esperado
- [ ] Métricas de retrieval: precision@k e recall@k (o doc certo veio?)
- [ ] Métrica de resposta: LLM-as-judge para groundedness (a resposta está apoiada no contexto?)
- [ ] `run_evals.py` gera um relatório; salvar o resultado para comparar entre versões
- [ ] Mudar uma coisa (chunk size ou top-k), rodar de novo e anotar o efeito
- [ ] Enviar as notas para o Langfuse via SDK (scores + Datasets/Experiments) e comparar versões no painel (D9)
- [ ] Experimento: ligar o LLM-as-judge gerenciado do Langfuse e comparar com o nosso juiz (D9)
- [ ] Confirmar a D9 em `docs/decisoes.md` com o que aprendeu

**Pronto quando:** você consegue dizer "mudei X, a métrica Y foi de A pra B".

## Fase 5 — Agent com LangGraph

Teoria de apoio: `p1-agent-engineering/agents/` e `p1-agent-engineering/langchain-langgraph/`

- [ ] `data/accesses.yaml` com acessos mínimos e sob demanda por projeto
- [ ] Tool `get_accesses` (código puro, com teste unitário)
- [ ] Transformar `search_docs` em tool
- [ ] Grafo LangGraph: nó do LLM → tools → volta ao LLM → resposta
- [ ] Resposta da API passa a incluir `tools_used` e `sources`
- [ ] Limite de iterações (o agent não pode entrar em loop)
- [ ] Prompt caching (`cache_control`) no system prompt + tools, quando o prefixo passar de 512 tokens. Validar com `cache_read` > 0 na 2ª chamada

**Pronto quando:** a pergunta "acessos + roadmap" chama as **duas** tools e o trace mostra isso.

## Fase 6 — Evals do agent

- [ ] Adicionar ao dataset a tool esperada para cada pergunta
- [ ] Métrica: % de acerto na escolha da tool
- [ ] Casos difíceis: pergunta fora do escopo, projeto que não existe, pergunta ambígua
- [ ] Rodar os evals antes e depois de mexer no prompt do agent

## Fase 7 — Produção

Teoria de apoio: `p1-production/` (docker-cicd, seguranca-llm, production-backend)

- [ ] Tratamento de erro: LLM fora do ar, timeout, resposta vazia
- [ ] API key no header + limite de tamanho da mensagem
- [ ] Guardrail básico: prompt injection nos docs/pergunta (ler `seguranca-llm/`)
- [ ] Dockerfile de produção (multi-stage, usuário não-root, healthcheck)
- [ ] CI simples (GitHub Actions rodando pytest)

## Fase 8 — Deploy na AWS

- [ ] Escolher o serviço (App Runner vs EC2 vs ECS) e registrar a decisão
- [ ] Secrets fora do código (variáveis de ambiente / Secrets Manager)
- [ ] Logs no CloudWatch
- [ ] URL pública funcionando

## Fase 9 — Fechamento

- [ ] README para portfólio: problema, arquitetura, decisões, métricas dos evals, como rodar
- [ ] Pitch de 2 minutos em inglês sobre o projeto
- [ ] (Opcional) Integração com Teams ou MCP

---

## O que o mercado pede → onde aparece aqui

| Requisito comum em vaga | Fase |
|---|---|
| Python + FastAPI + Pydantic | 0, 1 |
| Prompt engineering | 1 |
| LangChain / LangGraph | 1, 5 |
| RAG / vector store / embeddings | 3 |
| Evals / LLM-as-judge | 4, 6 |
| Observabilidade (Langfuse/LangSmith) | 2 |
| Agents / tool calling | 5 |
| Testes, Docker, CI | 0, 7 |
| AWS | 8 |
| Segurança de LLM | 7 |

---

## Log

| Data | O que fechou |
|------|--------------|
| 2026-10-22 | Projeto criado: roadmap + arquitetura + decisões pendentes |
| 2026-10-22 | Fase 0 fechada: compose (api + pgvector), `/health` 200/503, 2 testes passando |
| 2026-10-22 | Fase 1 fechada: `/chat` com Claude via LangChain, comparação de 3 prompts → v3 (D7) |
| 2026-10-23 | Fase 2 integrada: Langfuse via CallbackHandler, `session_id`/`user_id`, filtro contra span duplicado do SDK da Anthropic. Falta: abrir um trace e explicar cada campo |
