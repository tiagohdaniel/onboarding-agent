# onboarding-agent — instruções para o Claude

POC de assistente de onboarding (dados fictícios) para praticar a stack de AI Engineer:
FastAPI, LangChain/LangGraph, RAG com pgvector, evals, Langfuse, Docker. O objetivo final
é ter o que explicar em entrevista.

- Plano por fases: `ROADMAP.md`. Arquitetura: `ARQUITETURA.md`. Decisões: `docs/decisoes.md`. Conceitos: `docs/glossario.md`.
- Responder sempre em português.

## Modo de trabalho

- O Claude escreve o código completo e comentado; o Tiago lê e pergunta. Não entregar
  esqueleto com TODO, a não ser que ele peça.
- Rodar os testes (`uv run pytest -q`) e, quando mexer em dependência ou no `.env`,
  recriar o container (`docker compose up -d --build`).
- Ao fechar um item, marcar no `ROADMAP.md` e adicionar uma linha no log do fim do arquivo.

## Decisões sempre com tradeoff

Toda escolha relevante (biblioteca, arquitetura, prompt, configuração com alternativa real)
entra em `docs/decisoes.md` como `Dn`, no formato do topo do arquivo:
contexto → opções (prós/contras) → decisão → porquê → **tradeoff aceito** → **quando rever**
→ **frase de entrevista**.

- Nenhuma decisão sem "tradeoff aceito": se não perdemos nada, não era uma decisão.
- Quando o Claude apenas propõe e o Tiago ainda não confirmou, marcar 🟡 (proposta).
  As decisões são dele: apresentar as opções e a recomendação, não decidir sozinho.
- Ao explicar uma escolha na conversa, citar também o tradeoff, não só a vantagem.

## Profundidade: preparar para os follow-ups

Entrevista de IA desce de camada até achar onde o conhecimento acaba:
o quê → por quê → **como funciona por baixo** → **o que quebra** → **como você mede** → **e em escala**.

- Cada decisão em `docs/decisoes.md` tem **Follow-ups prováveis**: 2 a 3 perguntas das
  camadas de baixo, respondidas com o que aconteceu no projeto (números, erros vistos).
- Ao explicar algo na conversa, não parar na vantagem: incluir como funciona por baixo e
  o que quebra, de forma curta.
- Quando algo falhar ou surpreender (custo duplicado, cache que não ativou, regra de prompt
  que vazou), registrar no follow-up da decisão relacionada: "eu vi isso acontecer" vale
  mais que a definição.

## Glossário: ligar prática e teoria

- Todo conceito novo que aparecer (no código, na conversa ou numa decisão) entra em
  `docs/glossario.md`: **o que é** (simples), **exemplo** (analogia ou caso concreto) e
  **no projeto** (onde aparece, com ✔️ já usado ou 🔜 próxima fase).
- Siglas e termos técnicos no `decisoes.md` levam link para o glossário.
- Quando um termo 🔜 passar a ser usado de verdade, atualizar para ✔️ com o que aconteceu.

## Segurança

- Chaves (Anthropic, Langfuse) ficam só no `.env`, colocadas pelo próprio Tiago.
  Nunca pedir para colar chave na conversa, nunca imprimir o valor (só checar se está preenchida).
- `.env` sempre no `.gitignore` e no `.dockerignore`.

## Git

- Commit e push só quando ele pedir. Formato `tipo: descrição` (`feat`, `fix`, `docs`,
  `refactor`, `chore`), sem `Co-Authored-By` nem referência a IA.
- **Tudo do git em inglês**: mensagem de commit, nome de branch, tag, título e descrição
  de PR. Ex.: `feat: add pgvector retriever`. A conversa continua em português.

## README

- O `README.md` é a vitrine do projeto para recrutador. A cada implementação que muda o
  que o projeto faz (nova fase, nova tool, nova métrica de eval, mudança de arquitetura),
  atualizar o README no mesmo commit.
- Escrito em inglês (público internacional). Manter as seções: o que é, demo, arquitetura,
  stack, decisões-chave, resultados dos evals, como rodar, testes, roadmap.
- Números reais (métricas, latência, custo) entram assim que existirem; nada inventado.
