# Glossário

Os conceitos que aparecem no projeto, explicados de forma simples e ligados ao lugar onde
você viu (ou vai ver) cada um na prática.

**Formato de cada termo:**
- **O que é:** a explicação curta.
- **Exemplo:** uma analogia ou um caso concreto.
- **No projeto:** onde ele aparece aqui (arquivo, decisão ou fase).

Status no projeto: ✔️ já usamos · 🔜 vem numa próxima fase

## Índice

| Área | Termos |
|---|---|
| [LLM e API](#llm-e-api) | [Token](#token) · [Janela de contexto](#janela-de-contexto) · [max_tokens](#max_tokens) · [Mensagens system, human e ai](#mensagens-system-human-e-ai) · [Não determinismo](#não-determinismo) · [Prompt caching](#prompt-caching) · [Tool calling](#tool-calling) · [Provider e SDK](#provider-e-sdk) · [Lock-in](#lock-in) |
| [Prompt](#prompt) | [System prompt](#system-prompt) · [Few-shot](#few-shot) · [Alucinação](#alucinação) · [Vazamento de instrução](#vazamento-de-instrução) |
| [Observabilidade](#observabilidade) | [Trace](#trace) · [Span e generation](#span-e-generation) · [Session](#session) · [Callback](#callback) · [OpenTelemetry](#opentelemetry) · [Envio em lote (flush)](#envio-em-lote-flush) · [Score](#score) |
| [RAG e busca vetorial](#rag-e-busca-vetorial) | [RAG](#rag) · [Embedding](#embedding) · [Chunk e chunking](#chunk-e-chunking) · [Vector store](#vector-store) · [Similaridade de cosseno e distância L2](#similaridade-de-cosseno-e-distância-l2) · [Busca exata (kNN)](#busca-exata-knn) · [ANN](#ann) · [HNSW](#hnsw) · [IVFFlat](#ivfflat) · [Top-k](#top-k) · [Busca híbrida e BM25](#busca-híbrida-e-bm25) · [Metadado](#metadado) |
| [Evals](#evals) | [Eval](#eval) · [Golden dataset](#golden-dataset) · [Precision@k](#precisionk) · [Recall@k](#recallk) · [LLM-as-judge](#llm-as-judge) · [Groundedness](#groundedness) · [Rubrica](#rubrica) · [Vieses do juiz](#vieses-do-juiz) |
| [Python, API e infra](#python-api-e-infra) | [Lockfile e dependência transitiva](#lockfile-e-dependência-transitiva) · [Pydantic e validação](#pydantic-e-validação) · [Injeção de dependência](#injeção-de-dependência) · [Context manager (`with`)](#context-manager-with) · [Variável de ambiente](#variável-de-ambiente) · [Camadas e cache do Docker](#camadas-e-cache-do-docker) · [Volume](#volume) · [Healthcheck](#healthcheck) |
| [Dados e compliance](#dados-e-compliance) | [PII](#pii) · [LGPD](#lgpd) · [SaaS e self-host](#saas-e-self-host) · [AWS Bedrock](#aws-bedrock) |

---

## LLM e API

### Token

**O que é:** o pedaço de texto que o modelo lê e escreve. Não é uma palavra nem uma letra:
é um fragmento, que pode ser uma palavra curta inteira ou parte de uma palavra longa.

**Exemplo:** "onboarding" pode virar 2 ou 3 tokens. É por token que a API cobra, tanto na
entrada quanto na saída. Cada provider tem o seu tokenizador: o tiktoken é o da OpenAI e
não serve para contar tokens do Claude.

**No projeto:** ✔️ o `usage` do `/chat` e a rota `/chat/count-tokens`. Na Fase 1, a contagem
antes da chamada bateu exatamente com o que foi cobrado (531 = 531).

### Janela de contexto

**O que é:** o máximo de tokens que o modelo consegue considerar numa chamada, somando o
system prompt, o histórico, os documentos e a resposta.

**Exemplo:** é a "mesa de trabalho" do modelo. Se você coloca papel demais, algo tem que sair.

**No projeto:** 🔜 na Fase 3, o orçamento de tokens: contar os chunks antes de montar o
prompt e cortar se passar do limite.

### max_tokens

**O que é:** o limite de tokens da **resposta**. Não é o tamanho da janela de contexto.

**Exemplo:** com `max_tokens=10`, a resposta vem cortada no meio, e o `stop_reason` indica
`max_tokens` em vez de `end_turn` (fim natural).

**No projeto:** ✔️ `app/llm.py` (`max_tokens=4096`). Ver os follow-ups da
[D1](decisoes.md#d1--provider-do-llm).

### Mensagens system, human e ai

**O que é:** os papéis das mensagens numa chamada.
- **system:** as instruções fixas, que o usuário não vê.
- **human:** a pergunta do usuário.
- **ai:** a resposta do modelo.

Na API pura da Anthropic, os nomes são `system`, `user` e `assistant`.

**No projeto:** ✔️ `build_messages()` em `app/api.py`. No Langfuse, aparecem no campo
Input do trace.

### Não determinismo

**O que é:** a mesma pergunta pode gerar respostas diferentes a cada execução.

**Exemplo:** rodar o `compare_prompts.py` duas vezes não dá o mesmo texto. Por isso uma
comparação com poucas perguntas não prova nada sozinha.

**No projeto:** ✔️ é o motivo de a [D7](decisoes.md#d7--system-prompt-padrão) ficar para
ser confirmada com os evals da Fase 4.

### Prompt caching

**O que é:** a API guarda o processamento do começo do prompt (o prefixo) e, se a próxima
chamada começar exatamente igual, cobra cerca de 10% por essa parte. A gravação custa
1,25×, dura uns 5 minutos e só funciona acima de um mínimo de tokens.

**Exemplo:** o system prompt e as definições de tools são iguais em toda chamada: são o
prefixo ideal para o cache.

**No projeto:** ✔️ testado na Fase 1 (não ativou com o prompt pequeno, abaixo dos 512 tokens
mínimos do Haiku; ativou com um prompt maior). 🔜 Implementar na Fase 5.

### Tool calling

**O que é:** o modelo não executa nada. Ele **pede** para chamar uma função (nome +
argumentos em JSON), o seu código executa e devolve o resultado, e o modelo continua.

**Exemplo:** "quais acessos eu preciso?" → o modelo pede `get_accesses(projeto="Loja X")`
→ o código lê o YAML → o modelo responde com base no resultado.

**No projeto:** 🔜 Fase 5 (`search_docs` e `get_accesses`).

### Provider e SDK

**O que é:** o **provider** é a empresa que serve o modelo (Anthropic, OpenAI, AWS Bedrock).
O **SDK** é a biblioteca oficial para chamar a API dele (por exemplo, o pacote `anthropic`).

**No projeto:** ✔️ usamos o LangChain (`ChatAnthropic`), que usa o SDK `anthropic` por baixo.
Ver a [D1](decisoes.md#d1--provider-do-llm).

### Lock-in

**O que é:** ficar preso a um fornecedor porque sair dele custa caro (reescrever código,
migrar dados).

**No projeto:** ✔️ reduzido isolando o provider em `app/llm.py`.

---

## Prompt

### System prompt

**O que é:** as instruções fixas que definem o papel, as regras e o formato da resposta.

**No projeto:** ✔️ `app/agent/prompts.py` (v1, v2, v3). Ver a
[D7](decisoes.md#d7--system-prompt-padrão).

### Few-shot

**O que é:** colocar exemplos de pergunta e resposta dentro do prompt para o modelo imitar
o formato e o tom. "Zero-shot" é sem exemplo nenhum.

**No projeto:** ✔️ o exemplo do link do Jira na v3.

### Alucinação

**O que é:** o modelo inventa algo com cara de verdade: um link, um nome, um prazo.

**No projeto:** ✔️ a regra "nunca invente acessos, links, nomes ou prazos". 🔜 Na Fase 4, o
[groundedness](#groundedness) mede isso de forma automática.

### Vazamento de instrução

**O que é:** o nome que usamos aqui para quando uma regra do prompt aparece onde não devia.
O modelo tenta cumprir todas as instruções presentes, então uma regra sem condição vira
assunto.

**No projeto:** ✔️ a regra de senha da v3 apareceu em perguntas que não tinham nada a ver.
Ver a [D7](decisoes.md#d7--system-prompt-padrão).

---

## Observabilidade

### Trace

**O que é:** o registro completo de uma requisição: o que entrou, o que saiu, quanto tempo
levou e quanto custou.

**Exemplo:** é o "extrato" de uma chamada ao `/chat`.

**No projeto:** ✔️ cada `/chat` vira um trace no Langfuse
([D8](decisoes.md#d8--como-integrar-o-langfuse)).

### Span e generation

**O que é:** um **span** é um passo dentro do trace, com início e fim. Uma **generation** é
um span especial: uma chamada a um LLM, com modelo, tokens e custo.

**Exemplo:** na Fase 5, um trace terá vários spans: o agent decidindo, a busca no banco e
a chamada ao modelo.

**No projeto:** ✔️ hoje cada trace tem uma generation (`ChatAnthropic`).

### Session

**O que é:** um agrupamento de traces da mesma conversa.

**No projeto:** ✔️ o campo `session_id` do `/chat`. Na aba Sessions do Langfuse.

### Callback

**O que é:** uma função (ou objeto) que você entrega a uma biblioteca para ela chamar
quando algo acontecer.

**Exemplo:** "quando a chamada ao modelo começar e terminar, avise este objeto".

**No projeto:** ✔️ o `CallbackHandler` do Langfuse, passado em
`config={"callbacks": [...]}` no `/chat`.

### OpenTelemetry

**O que é:** um padrão aberto para gerar e enviar traces e spans. Várias ferramentas
(Langfuse, Datadog, Grafana) entendem esse formato.

**No projeto:** ✔️ o Langfuse é construído sobre ele, e o SDK da Anthropic também gera spans
nesse padrão. Foi isso que duplicou o custo
([D8](decisoes.md#d8--como-integrar-o-langfuse)).

### Envio em lote (flush)

**O que é:** em vez de mandar cada trace na hora, o SDK junta vários e envia em segundo
plano. O **flush** força o envio do que está guardado.

**Exemplo:** é por isso que o trace demora alguns segundos para aparecer, e que um script
curto precisa chamar `flush()` antes de terminar.

**No projeto:** ✔️ o Langfuse envia a cada ~5s.

### Score

**O que é:** uma nota presa a um trace. Pode vir de um LLM juiz, de código, de uma pessoa
ou do 👍/👎 do usuário.

**No projeto:** 🔜 Fase 4 ([D9](decisoes.md#d9--onde-rodam-os-evals)).

---

## RAG e busca vetorial

### RAG

**O que é:** Retrieval-Augmented Generation. Antes de o modelo responder, você **busca** os
trechos relevantes dos seus documentos e os coloca no prompt. O modelo responde com base
neles.

**Exemplo:** é uma prova com consulta: em vez de responder de memória, o modelo recebe as
páginas certas do livro.

**No projeto:** 🔜 Fase 3 (tool `search_docs`).

### Embedding

**O que é:** uma lista de números (um vetor, com centenas ou milhares de posições) que
representa o **significado** de um texto. Textos com sentido parecido geram vetores
próximos.

**Exemplo:** "como peço acesso ao Jira?" e "preciso de permissão no Jira" ficam perto, mesmo
sem palavras iguais.

**No projeto:** 🔜 Fase 3. A escolha do modelo é a [D5](decisoes.md#d5--modelo-de-embedding).

### Chunk e chunking

**O que é:** **chunking** é dividir um documento em pedaços menores (**chunks**) antes de
gerar os embeddings. A busca devolve chunks, não documentos inteiros.

**Exemplo:** chunk grande demais traz assunto misturado; chunk pequeno demais corta a
resposta no meio.

**No projeto:** 🔜 Fase 3. Na Fase 4, mudar o tamanho do chunk e medir o efeito.

### Vector store

**O que é:** o banco que guarda os embeddings e sabe buscar os mais próximos de um vetor.

**No projeto:** ✔️ o pgvector no Docker Compose
([D3](decisoes.md#d3--vector-store)). Os dados entram na Fase 3.

### Similaridade de cosseno e distância L2

**O que é:** duas formas de medir se dois vetores estão perto.
- **Cosseno:** olha o **ângulo** entre eles. 1 significa mesma direção (mesmo sentido).
- **L2 (euclidiana):** a distância em linha reta entre os pontos.

Se os vetores forem **normalizados** (todos com o mesmo tamanho), as duas dão a mesma ordem
de resultados.

**No projeto:** 🔜 Fase 3, junto com a [D5](decisoes.md#d5--modelo-de-embedding).

### Busca exata (kNN)

**O que é:** k-Nearest Neighbors. Compara a pergunta com **todos** os vetores e devolve os
k mais próximos. O resultado é perfeito, mas fica lento com muitos vetores.

**Exemplo:** procurar um livro olhando todos os livros da biblioteca, um por um.

**No projeto:** 🔜 é o que o pgvector faz quando a tabela não tem índice.

### ANN

**O que é:** Approximate Nearest Neighbors (vizinhos mais próximos aproximados). Em vez de
comparar com todos os vetores, um índice olha só uma parte promissora. É muito mais rápido,
mas pode deixar escapar algum vizinho bom: troca-se um pouco de [recall](#recallk) por
velocidade.

**Exemplo:** na biblioteca, você vai direto à estante do assunto. Quase sempre acha o livro,
mas se ele estiver na estante errada, você não vê.

**No projeto:** 🔜 Fase 3, ao criar o índice no pgvector. Ver os follow-ups da
[D3](decisoes.md#d3--vector-store).

### HNSW

**O que é:** Hierarchical Navigable Small World. Um índice [ANN](#ann) em forma de grafo com
camadas: as de cima têm poucos pontos e permitem "saltos" longos; as de baixo têm todos os
pontos e refinam a busca.

**Exemplo:** como achar um endereço: primeiro o país, depois a cidade, depois a rua.

**Tradeoff:** busca rápida e boa precisão, mas usa mais memória e demora mais para construir.

**No projeto:** 🔜 Fase 3 (provável escolha de índice).

### IVFFlat

**O que é:** um índice [ANN](#ann) que divide os vetores em grupos (clusters). Na busca, ele
olha só os grupos mais próximos da pergunta.

**Exemplo:** a biblioteca dividida em seções; você só entra nas 2 ou 3 seções mais
parecidas com o que procura.

**Tradeoff:** construção rápida e menos memória, mas precisão menor que o HNSW, e precisa de
dados já carregados para formar bons grupos.

**No projeto:** 🔜 Fase 3 (alternativa ao HNSW).

### Top-k

**O que é:** quantos resultados a busca devolve (os k mais próximos).

**Exemplo:** k pequeno pode deixar o chunk certo de fora; k grande traz ruído e gasta tokens.

**No projeto:** 🔜 Fase 3. Na Fase 4, mudar o k e medir o efeito.

### Busca híbrida e BM25

**O que é:** o **BM25** é a busca clássica por palavra-chave (como um buscador antigo). A
**busca híbrida** combina BM25 e busca vetorial: uma acha a palavra exata (um código de
erro, uma sigla), a outra acha o sentido.

**No projeto:** 🔜 possível evolução depois da Fase 3; é um dos sinais de "quando rever" da
[D3](decisoes.md#d3--vector-store).

### Metadado

**O que é:** informação sobre o chunk que não é o texto em si: projeto, nome do arquivo,
data.

**Exemplo:** buscar só nos documentos do projeto "Loja X" com um `WHERE projeto = 'loja-x'`.

**No projeto:** 🔜 Fase 3. É uma das vantagens do pgvector
([D3](decisoes.md#d3--vector-store)).

---

## Evals

### Eval

**O que é:** um teste automático da **qualidade** do sistema de IA. Diferente de um teste
unitário, ele não dá só passou/falhou: dá uma nota, que você compara entre versões.

**No projeto:** 🔜 Fase 4. O `compare_prompts.py` foi uma versão manual.

### Golden dataset

**O que é:** o conjunto de perguntas com a resposta certa já conhecida (o gabarito).

**No projeto:** 🔜 `evals/dataset.jsonl` na Fase 4: pergunta, resposta esperada e doc esperado.

### Precision@k

**O que é:** dos k chunks que a busca trouxe, quantos eram relevantes.

**Exemplo:** a busca trouxe 5 chunks e 2 eram úteis → precision@5 = 2/5 = 0,4.

**No projeto:** 🔜 Fase 4.

### Recall@k

**O que é:** de todos os chunks relevantes que existem, quantos apareceram entre os k
primeiros.

**Exemplo:** existem 2 chunks certos e só 1 veio no top-5 → recall@5 = 1/2 = 0,5. No RAG,
costuma importar mais que a precision: se o chunk certo não veio, o modelo não tem como
acertar.

**No projeto:** 🔜 Fase 4. É o que o [ANN](#ann) pode piorar um pouco.

### LLM-as-judge

**O que é:** usar um LLM para dar nota à resposta de outro LLM, seguindo uma
[rubrica](#rubrica).

**No projeto:** 🔜 Fase 4 ([D9](decisoes.md#d9--onde-rodam-os-evals)).

### Groundedness

**O que é:** se a resposta está **apoiada** no contexto que o modelo recebeu, ou se ele
inventou algo além dele.

**Exemplo:** o chunk diz "peça acesso ao tech lead" e a resposta diz "peça ao gerente" →
resposta não fundamentada.

**No projeto:** 🔜 Fase 4.

### Rubrica

**O que é:** os critérios explícitos que o juiz usa para dar a nota. Quanto mais objetivos
(sim/não por critério), mais confiável a nota.

**No projeto:** 🔜 Fase 4.

### Vieses do juiz

**O que é:** tendências conhecidas do LLM-as-judge:
- prefere respostas mais longas;
- favorece respostas do mesmo modelo;
- muda a nota conforme a ordem, quando compara duas respostas.

**No projeto:** 🔜 Fase 4. Ver os follow-ups da [D9](decisoes.md#d9--onde-rodam-os-evals).

---

## Python, API e infra

### Lockfile e dependência transitiva

**O que é:** a **dependência transitiva** é a dependência da sua dependência (o
`langchain-anthropic` traz o `anthropic`, que traz o `httpx`...). O **lockfile** grava a
versão exata de todas elas, para qualquer máquina instalar igual.

**No projeto:** ✔️ `uv.lock` ([D2](decisoes.md#d2--gerenciador-de-pacotes)).

### Pydantic e validação

**O que é:** o Pydantic converte e valida dados a partir das anotações de tipo da classe.
Se o dado não bate, ele gera um erro explicando o porquê.

**No projeto:** ✔️ `ChatRequest` (mensagem vazia → 422) e o `Settings` em `app/config.py`.

### Injeção de dependência

**O que é:** a função não cria o que precisa; ela **recebe** pronto. Assim dá para trocar a
peça sem mexer na função.

**Exemplo:** nos testes, trocamos o LLM de verdade por um falso sem alterar o `/chat`.

**No projeto:** ✔️ `Depends(get_llm)` e `Depends(get_langfuse_handler)` no `app/api.py`, e
o `dependency_overrides` nos testes.

### Context manager (`with`)

**O que é:** um objeto que faz algo ao **entrar** num bloco e desfaz ao **sair**, mesmo se
der erro no meio. O `with` garante essa saída (é um `try/finally` embutido).

**Exemplo:** `with open("x.txt") as f:` fecha o arquivo no fim, mesmo com exceção.

**No projeto:** ✔️ `with psycopg.connect(...)` no `check_db` (fecha a conexão) e
`with propagate_attributes(...)` no `/chat` (liga `session_id`/`user_id` aos traces só
durante aquela requisição e depois limpa).

### Variável de ambiente

**O que é:** uma configuração que vem de fora do código (do sistema ou do container). O
`.env` é só um arquivo que preenche essas variáveis.

**Exemplo:** uma variável de ambiente de verdade vence o `.env`, e é assim que o
`conftest.py` desliga o Langfuse nos testes.

**No projeto:** ✔️ `.env`, `app/config.py` e o `environment:` do `docker-compose.yml`.

### Camadas e cache do Docker

**O que é:** cada instrução do Dockerfile gera uma camada. Se nada mudou numa camada, o
Docker reaproveita a anterior em vez de refazer.

**Exemplo:** copiar o `uv.lock` antes do código faz o `uv sync` só rodar de novo quando as
dependências mudam.

**No projeto:** ✔️ `Dockerfile` ([D2](decisoes.md#d2--gerenciador-de-pacotes)).

### Volume

**O que é:** uma pasta que fica fora do container e sobrevive a ele ser recriado.

**No projeto:** ✔️ o `pgdata` (os dados do Postgres) e o `./app` montado para o hot reload.

### Healthcheck

**O que é:** um teste periódico que diz se um serviço está pronto.

**No projeto:** ✔️ o `pg_isready` do banco (a API só sobe com o banco saudável) e a rota
`/health` (200 ou 503).

---

## Dados e compliance

### PII

**O que é:** Personally Identifiable Information. Dado que identifica uma pessoa: nome, CPF,
e-mail, telefone.

**No projeto:** 💡 mascarar PII antes de mandar o trace é uma das opções da
[D6](decisoes.md#d6--caminho-para-dado-real).

### LGPD

**O que é:** a lei brasileira de proteção de dados pessoais. Define o que pode ser coletado,
com que base legal, onde é guardado e com quem é compartilhado.

**No projeto:** 💡 o motivo de a [D6](decisoes.md#d6--caminho-para-dado-real) existir.

### SaaS e self-host

**O que é:** no **SaaS**, o fornecedor roda o serviço e você só usa (Langfuse Cloud). No
**self-host**, você roda o serviço na sua infra (Langfuse em containers da empresa).

**Atenção:** self-host não significa "não exposto na internet". Isso depende da rede.

**No projeto:** ✔️ [D4](decisoes.md#d4--observabilidade) e
[D6](decisoes.md#d6--caminho-para-dado-real).

### AWS Bedrock

**O que é:** o serviço da AWS que oferece modelos de vários fornecedores (inclusive o
Claude) rodando na infraestrutura da AWS, sob o contrato da empresa com a AWS.

**No projeto:** 💡 o caminho para dado real na [D6](decisoes.md#d6--caminho-para-dado-real).
