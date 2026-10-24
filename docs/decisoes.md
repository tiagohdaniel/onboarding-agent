# Registro de decisões

Toda escolha relevante entra aqui. Na entrevista, "por que você escolheu X e não Y?"
se responde com este arquivo.

📖 Termo que não ficou claro? Os links levam ao [glossário](glossario.md), que liga cada
conceito ao lugar onde ele aparece no projeto.

## Índice

| # | Tema | Status | Escolha |
|---|---|---|---|
| [D1](#d1--provider-do-llm) | Provider do LLM | ✅ | Claude via LangChain (Haiku) |
| [D2](#d2--gerenciador-de-pacotes) | Gerenciador de pacotes | ✅ | uv |
| [D3](#d3--vector-store) | Vector store | ✅ | pgvector no Docker Compose |
| [D4](#d4--observabilidade) | Observabilidade | ✅ | Langfuse Cloud |
| [D5](#d5--modelo-de-embedding) | Modelo de embedding | ⏳ | Decidir na Fase 3 |
| [D6](#d6--caminho-para-dado-real) | Caminho para dado real | 💡 | Anotação para o futuro |
| [D7](#d7--system-prompt-padrão) | System prompt padrão | ✅ | v3 |
| [D8](#d8--como-integrar-o-langfuse) | Integração do Langfuse | ✅ | `CallbackHandler` + filtro de spans |
| [D9](#d9--onde-rodam-os-evals) | Onde rodam os evals | 🟡 | Proposta: no código + scores no Langfuse |

**Status:** ✅ decidido · 🟡 proposta (falta confirmar) · ⏳ pendente · 💡 anotação

## Como ler cada decisão

| Seção | O que responde |
|---|---|
| **Contexto** | Qual problema precisava de escolha |
| **Opções** | Prós e contras de cada alternativa |
| ✅ **Decisão** | O que escolhemos |
| 💡 **Porquê** | O motivo |
| ⚖️ **Tradeoff aceito** | O que perdemos ao escolher isso (não existe escolha sem custo) |
| 🔁 **Quando rever** | O sinal concreto que faria a decisão mudar |
| 🎤 **Frase de entrevista** | A resposta curta, em uma ou duas frases |
| ❓ **Follow-ups prováveis** | As perguntas que vêm depois: como funciona por baixo, o que quebra, como medir |

---

## D1 · Provider do LLM

> ✅ Decidido em 2026-10-22

**Contexto:** o agent precisa de um LLM com bom tool calling.

| Opção | Prós | Contras |
|---|---|---|
| **Anthropic (Claude)** | Muito bom em tool calling; você já usa no dia a dia | Pago por uso |
| OpenAI | É o que mais aparece em vaga e em tutorial | Pago por uso |
| Modelo local (Ollama) | De graça, roda offline | Mais fraco em tool calling e lento na máquina local |

### ✅ Decisão

Claude (Anthropic) via LangChain, com o modelo configurável no `.env` (hoje `claude-haiku-5-5`).

### 💡 Porquê

É uma POC com dados fictícios, então custo e lock-in não pesam agora. Como o modelo é
criado em um lugar só (`app/llm.py`), trocar de provider depois é simples.

### ⚖️ Tradeoff aceito

- Os dados saem para a API da Anthropic.
- Uma camada a mais (LangChain) entre o código e a API: recurso novo da Anthropic pode
  demorar a chegar nele.

### 🔁 Quando rever

- Dado real de cliente (ver [D6](#d6--caminho-para-dado-real)).
- Custo por conversa alto demais.

### 🎤 Frase de entrevista

> "Isolei o provider numa função só; o resto do código conhece apenas a interface
> `BaseChatModel`. Trocar de modelo é configuração, trocar de provider é mudar um arquivo,
> mas sempre rodando os evals de novo."

### ❓ Follow-ups prováveis

**1. "Se trocar de Claude para GPT, o que quebra?"**

O código muda só no `llm.py`, mas o comportamento não é portável: o mesmo prompt responde
diferente, a contagem de tokens é de cada provider e o `cache_control` (Fase 5) é da
Anthropic. Por isso a troca só vale depois de rodar os evals.

**2. "Por que Haiku e não Opus?"**

Custo: $0,10/$0,50 contra $4/$20 por milhão de tokens (40× mais barato). Para respostas
curtas de onboarding, o Haiku basta. Quem confirma isso são os evals, não a intuição.

**3. "O que fazem o `max_tokens=4096` e o `timeout=60`?"**

O [`max_tokens`](glossario.md#max_tokens) limita só a **saída**: se estourar, a resposta vem cortada (`stop_reason` =
`max_tokens`). Não é o tamanho do contexto. O `timeout` evita uma requisição pendurada
segurando o worker.

---

## D2 · Gerenciador de pacotes

> ✅ Decidido em 2026-10-22

**Contexto:** instalar dependências de forma reproduzível no local, no CI e no Docker.

| Opção | Prós | Contras |
|---|---|---|
| **`uv`** | Rápido, moderno, cada vez mais comum em vaga | Mais uma ferramenta pra aprender |
| `pip` + `venv` + `requirements.txt` | Você já conhece, é universal | Sem lockfile de verdade |
| Poetry | Lockfile, maduro | Mais lento, está perdendo espaço para o uv |

### ✅ Decisão

uv.

### 💡 Porquê

O `uv.lock` garante que local, CI e container instalam exatamente as mesmas versões.
De quebra, o build do Docker fica mais rápido.

### ⚖️ Tradeoff aceito

- Ferramenta mais nova: parte dos tutoriais e times ainda usa pip.
- Quem pegar o projeto precisa instalar o uv.

### 🔁 Quando rever

- Se a empresa padronizar outra ferramenta.

### 🎤 Frase de entrevista

> "Uso uv pelo lockfile: o mesmo `uv.lock` no meu notebook, no CI e na imagem Docker.
> O pip sozinho não garante isso."

### ❓ Follow-ups prováveis

**1. "O que o lockfile resolve que o `requirements.txt` não resolve?"**

O `uv.lock` guarda a árvore inteira, incluindo as [dependências das dependências](glossario.md#lockfile-e-dependência-transitiva), com
versão exata e hash. Um `requirements.txt` comum fixa só o que você escreveu, e o resto é
resolvido de novo a cada instalação.

**2. "Por que `uv sync --frozen --no-install-project` no Dockerfile?"**

O `--frozen` falha se o lock estiver desatualizado, em vez de resolver de novo em
silêncio. E copiar só o `pyproject.toml` e o `uv.lock` antes do código aproveita o [cache de
camadas do Docker](glossario.md#camadas-e-cache-do-docker): mudar o código não reinstala as dependências.

---

## D3 · Vector store

> ✅ Decidido em 2026-10-22

**Contexto:** guardar os embeddings dos documentos para o RAG (Fase 3).

| Opção | Prós | Contras |
|---|---|---|
| Chroma (local, em arquivo) | Zero infra, ótimo pra POC | Não é o que se usa em produção grande |
| **pgvector (Postgres no Docker)** | Muito usado em produção, junta SQL + vetor | Precisa subir o Postgres desde o início |
| FAISS | Simples, em memória | Não persiste sozinho, não filtra metadado |
| Banco vetorial gerenciado (Pinecone etc.) | Escala sem operar nada | Pago, dados saem, mais um fornecedor |

### ✅ Decisão

pgvector (Postgres) num container separado, com todo o ambiente em Docker Compose.

### 💡 Porquê

- Fica mais perto de um ambiente real: o banco é um serviço à parte, não um arquivo dentro
  da aplicação.
- Junta SQL + vetor no mesmo lugar (filtro por metadado com SQL normal).
- Dá prática de Docker desde o começo.

### ⚖️ Tradeoff aceito

- Subir e manter o Postgres desde a Fase 0.
- Em volume muito grande (dezenas de milhões de vetores), um banco vetorial dedicado tende
  a ser mais rápido.

### 🔁 Quando rever

- Latência de busca alta com muitos documentos.
- Necessidade de busca híbrida que o Postgres não atenda bem.

### 🎤 Frase de entrevista

> "Escolhi pgvector porque a maioria das empresas já tem Postgres: não é um banco novo para
> operar, e o filtro por metadado é SQL comum."

### ❓ Follow-ups prováveis

**1. "Como o pgvector acha os vizinhos rápido?"**

Sem índice, ele compara com todos os vetores: busca exata, lenta em volume. Com índice, a
busca é **aproximada** ([ANN](glossario.md#ann)):

- **[HNSW](glossario.md#hnsw):** um grafo em camadas. Boa precisão, mas usa mais memória e o build é mais lento.
- **[IVFFlat](glossario.md#ivfflat):** divide os vetores em grupos. Build rápido, precisão menor.

Nos dois casos, troca-se um pouco de [recall](glossario.md#recallk) por velocidade.

**2. "Cosseno ou distância L2?"**

Depende do modelo de embedding ([D5](#d5--modelo-de-embedding)). Com vetores
normalizados, as duas dão a mesma ordem de resultados
([cosseno e L2 no glossário](glossario.md#similaridade-de-cosseno-e-distância-l2)).

**3. "Por que o banco num container separado?"**

Ciclo de vida próprio: o volume persiste quando a API reinicia, e o healthcheck faz a API
só subir com o banco pronto.

---

## D4 · Observabilidade

> ✅ Decidido em 2026-10-22

**Contexto:** ver prompt, resposta, tokens, custo e latência de cada chamada.

| Opção | Prós | Contras |
|---|---|---|
| **Langfuse Cloud (free tier)** | Open source, integra com LangChain, não precisa subir nada | Dados vão para a nuvem deles |
| Langfuse self-host (Docker) | Controle total, aprende a operar | Mais containers para manter |
| LangSmith | Nativo do LangChain, aparece em vaga | Fechado, free tier limitado |
| Só logs no terminal | Zero dependência | Sem custo por chamada, sem sessão, sem comparação |

### ✅ Decisão

Langfuse Cloud (região US).

### 💡 Porquê

Integra com o LangChain via callback, e os traces ficam na nuvem como num ambiente real:
a equipe toda vê, sem depender da máquina de ninguém.

### ⚖️ Tradeoff aceito

- O trace inteiro (prompt, resposta e, depois, os chunks) fica armazenado fora da nossa
  infra.
- Há um atraso de alguns segundos até o trace aparecer no painel.

### 🔁 Quando rever

- Dado real de cliente (ver [D6](#d6--caminho-para-dado-real)).
- Limite do free tier.

### 🎤 Frase de entrevista

> "Usei Langfuse Cloud porque os dados eram fictícios. Com dado real, eu iria de self-host
> ou mascararia [PII](glossario.md#pii) antes de enviar."

### ❓ Follow-ups prováveis

**1. "O Langfuse deixa a requisição mais lenta?"**

Não: os traces vão num [lote](glossario.md#envio-em-lote-flush), em segundo plano, a cada ~5s. O risco é o contrário: se o
processo morrer antes do envio, o trace se perde. Em script curto é preciso chamar
`flush()` no fim.

**2. "O que você olha primeiro num trace?"**

O input completo (o que o modelo realmente recebeu), depois os tokens e a latência. No RAG,
os chunks que vieram: a maioria dos erros de resposta começa numa busca ruim.

**3. "E a LGPD?"**

Ver [D6](#d6--caminho-para-dado-real): o Langfuse **armazena** o trace inteiro, então com
dado real entra self-host ou mascaramento de PII.

---

## D5 · Modelo de embedding

> ⏳ Decidir na Fase 3

---

## D6 · Caminho para dado real

> 💡 Anotação para o futuro, não decidido

**Contexto:** na POC, o Claude (API da Anthropic) e o Langfuse Cloud recebem os dados fora
da nossa infraestrutura. Com dados fictícios, tudo bem. Com dado real de cliente ou da
empresa, contrato (NDA, residência de dados), LGPD e a política interna de IA podem barrar.

### 🎯 O ponto central

- O Langfuse **armazena** o trace inteiro (prompt, chunks, resposta).
- O provider do LLM **processa** (e pode reter por um tempo, conforme os termos).

### Opções

| Peça | Opção | O que resolve | Custo |
|---|---|---|---|
| LLM | AWS Bedrock (Claude na conta AWS da empresa) | O modelo roda na infra da AWS, sob o contrato que a empresa já tem; IAM, região escolhida, VPC endpoint (tráfego privado); o provider do modelo não vê os prompts | Troca `ChatAnthropic` → `ChatBedrock` no `app/llm.py`; nem todo modelo/versão está em toda região |
| Observabilidade | Langfuse self-host | Os traces ficam no banco da empresa | Operar Postgres + ClickHouse + Redis + storage S3 |
| Observabilidade | Mascarar PII antes do trace | Reduz o que sai, mesmo usando SaaS | Regra de mascaramento pode deixar passar algo |
| Ambos | Revisar os termos do provider | Saber se treina com os dados e quanto tempo retém | — |

### ⚠️ Atenção

Self-host **não** é o mesmo que "não exposto". Onde os dados ficam (controle) e quem
acessa pela rede (subnet privada, VPN, firewall, SSO) são decisões separadas.

### 🎤 Frase de entrevista

> "SaaS é mais simples, mas os dados saem. Self-host mantém os dados, mas você opera a
> infra. A exposição de rede é uma terceira decisão."

---

## D7 · System prompt padrão

> ✅ Decidido em 2026-10-22

**Contexto:** comparação de 3 versões com as mesmas 5 perguntas, usando o Haiku
(`experiments/prompts-2026-10-22-1700.md`).

| Versão | O que tem | Resultado |
|---|---|---|
| v1 | Só regras ("não invente") | Não inventou, mas é o mais longo e o mais genérico |
| v2 | + formato fixo (Resumo/Passos/Com quem falar) | Consistente, fácil de comparar |
| **v3** | + "diga logo se falta dado" + regra de senha + exemplo ([few-shot](glossario.md#few-shot)) | Saída mais curta e rápida; entrada 2,3× maior, custo total empatado |

### ✅ Decisão

v3, com a regra de senha restrita a perguntas sobre credenciais.

### 💡 Porquê

- Respostas curtas e no mesmo formato, o que é bom para os evals da Fase 4.
- Sem alucinação.
- No teste, a regra de senha "vazou" para perguntas que não tinham nada a ver (1 e 5).
  Por isso ela foi reescrita para valer só quando o assunto é credencial.

### ⚖️ Tradeoff aceito

- Prompt de entrada 2,3× maior: mais tokens por chamada.
- O formato fixo deixa a resposta menos natural numa conversa casual.
- Cada regra nova no prompt pode "vazar" para onde não devia, como aconteceu com a de senha.

### 🔁 Quando rever

- Quando os evals da Fase 4 existirem: aí a comparação deixa de ser no olho.

### 📏 A medir

- Se o ajuste eliminou o vazamento (rodar o script de novo).

### 🎤 Frase de entrevista

> "Comparei três versões do prompt com as mesmas perguntas, medindo tokens, latência e se o
> modelo inventava. Escolhi pela evidência, não pelo gosto."

### ❓ Follow-ups prováveis

**1. "Cinco perguntas é amostra pequena. Como você sabe que a v3 é melhor?"**

Não sabe com certeza: foi uma comparação no olho, e o LLM não é determinístico (a mesma
pergunta varia entre execuções; ver [não determinismo](glossario.md#não-determinismo)). É exatamente por isso que existe a Fase 4, com dataset e
métrica.

**2. "Por que a entrada cresceu 2,3× e o custo empatou?"**

No Haiku, o token de saída custa 5× o de entrada ($0,50 contra $0,10), e a v3 gerou
respostas mais curtas. Ganhou na saída o que perdeu na entrada.

**3. "Por que a regra de senha vazou?"**

O modelo tenta cumprir todas as instruções que estão no prompt; uma regra sem condição
vira assunto. A correção foi condicionar ("somente quando a pergunta for sobre senhas") e
medir de novo.

---

## D8 · Como integrar o Langfuse

> ✅ Decidido em 2026-10-23

**Contexto:** registrar cada chamada ao LLM no Langfuse ([D4](#d4--observabilidade)) sem
espalhar código de tracing pela aplicação.

| Opção | Prós | Contras |
|---|---|---|
| **`CallbackHandler` do LangChain** | Poucas linhas; captura input, output, tokens e custo sozinho; funciona igual no LangGraph (Fase 5) | Depende do LangChain; só registra o que passa por ele |
| Decorator `@observe` do Langfuse | Rastreia qualquer função Python, não só o LLM | Mais um lugar para lembrar de decorar |
| Registrar na mão (spans manuais) | Controle total do que vai | Muito código; fácil esquecer um campo |

### ✅ Decisão

- `CallbackHandler`, criado em `app/observability.py` e injetado no `/chat` via `Depends`.
- `session_id` e `user_id` via `propagate_attributes`.
- Exportação filtrada com `should_export_span=is_langfuse_span`.

### 💡 Porquê

- É o caminho mais curto e é o mesmo mecanismo que o LangGraph vai usar.
- O filtro existe porque o SDK da Anthropic também gera [spans](glossario.md#span-e-generation) próprios ([OpenTelemetry](glossario.md#opentelemetry)):
  sem ele, cada chamada aparecia duas vezes e com custo em dobro.

### ⚖️ Tradeoff aceito

- O filtro descarta qualquer span que não seja do Langfuse, incluindo o detalhe HTTP da
  chamada à Anthropic.
- O que não passa pelo LangChain (ex.: consulta ao banco) não aparece no trace sem
  `@observe`.

### 🔁 Quando rever

- Se precisarmos rastrear passos fora do LangChain (aí entra o `@observe`).
- Se outra biblioteca instrumentada precisar aparecer no trace.

### 🎤 Frase de entrevista

> "Integrei via callback, sem tocar na lógica. E vi o custo duplicado no painel: dois
> instrumentadores registrando a mesma chamada. Resolvi filtrando a exportação."

### ❓ Follow-ups prováveis

**1. "Como o callback funciona por baixo?"**

O LangChain dispara eventos (início e fim da chamada ao modelo) para os handlers da lista
`callbacks`. O handler do Langfuse transforma esses eventos em spans do OpenTelemetry, que
são enviados em lote.

**2. "Por que o custo duplicou?"**

O SDK da Anthropic tem instrumentação OpenTelemetry própria, e o Langfuse (que é construído
sobre OpenTelemetry) exporta por padrão qualquer span de LLM. Eram duas fontes registrando
a mesma chamada. O filtro deixa sair só os spans do Langfuse.

**3. "Por que o tracing fica desligado nos testes?"**

Teste não pode depender de rede nem poluir o painel com chamadas do modelo falso. O
`conftest.py` zera a chave antes do app ser importado.

---

## D9 · Onde rodam os evals

> 🟡 Proposta, confirmar na Fase 4

**Contexto:** a Fase 4 precisa dar nota para o retrieval (o doc certo veio?) e para a
resposta ([groundedness](glossario.md#groundedness)). O Langfuse oferece um [LLM-as-judge](glossario.md#llm-as-judge) gerenciado, rodando no próprio
painel.

| Opção | Prós | Contras |
|---|---|---|
| **Evals no código (`run_evals.py`) + scores enviados ao Langfuse via SDK** | Lógica e prompt do juiz versionados no git; reproduzível no CI; métricas exatas (recall@k) sem LLM | Mais código para escrever |
| Juiz gerenciado do Langfuse | Zero código; templates prontos (alucinação, relevância); roda sozinho nos traces de produção | Exige cadastrar chave de LLM no Langfuse; config fica no painel, fora do git; mais uma chamada paga por trace avaliado |
| Só anotação humana | Nota mais confiável | Não escala; ninguém faz toda semana |

### 🟡 Proposta

- Evals no código, com as notas enviadas ao Langfuse (Datasets/Experiments para comparar
  versões).
- Depois, como experimento, ligar o juiz gerenciado nos traces e comparar com o nosso.

### 💡 Porquê

O eval vira parte do código, roda igual em qualquer máquina e no CI, e o Langfuse fica só
para visualizar e comparar.

### ⚖️ Tradeoff aceito

- Escrevemos e mantemos o juiz nós mesmos.
- Não temos avaliação automática contínua de produção até ligar o gerenciado.

### 🔁 Quando rever

- Com tráfego real, quando valer avaliar amostras de produção sem rodar script.

### 🎤 Frase de entrevista

> "O eval mora no código e versiona junto com o prompt. A ferramenta de observabilidade é
> onde eu enxergo e comparo os resultados, não onde a lógica vive."

### ❓ Follow-ups prováveis

**1. "Você confia na nota do LLM-as-judge?"**

Não às cegas. O juiz tem [vieses conhecidos](glossario.md#vieses-do-juiz): prefere respostas mais longas, tende a
favorecer respostas do mesmo modelo e é sensível à ordem quando compara duas. Mitigações:

- Rubrica objetiva (sim/não por critério).
- Juiz diferente do modelo avaliado.
- Conferir uma amostra com nota humana para medir a concordância.

**2. "Por que não usar só métrica exata?"**

Recall@k mede a busca, mas não diz se a resposta usou o contexto certo. Groundedness
precisa de alguém (ou algo) que leia a resposta.
