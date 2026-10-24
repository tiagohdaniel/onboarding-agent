import psycopg
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langfuse import propagate_attributes
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel, Field

from app.agent.prompts import SYSTEM_PROMPT
from app.config import settings
from app.llm import get_llm
from app.observability import get_langfuse_handler

app = FastAPI(title="Onboarding Agent")


class ChatRequest(BaseModel):
    # Validação de graça: vazio ou gigante → 422 antes de gastar token
    message: str = Field(min_length=1, max_length=2000)
    # Opcionais: só servem para agrupar e filtrar os traces no Langfuse
    session_id: str | None = None
    user_id: str | None = None


class Usage(BaseModel):
    # Tokens que a API cobrou nessa chamada (vem do usage_metadata da resposta)
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    answer: str
    usage: Usage


class CountTokensResponse(BaseModel):
    input_tokens: int


def build_messages(user_message: str) -> list[BaseMessage]:
    """Monta o que vai pro LLM. Usado no /chat e no /chat/count-tokens (os dois contam igual)."""
    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]


def check_db() -> bool:
    """Retorna True se o banco responde, False se não."""
    try:
        # "with" fecha a conexão sozinho no fim, mesmo se der erro
        with psycopg.connect(settings.database_url, connect_timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except psycopg.OperationalError:
        # banco fora do ar, timeout, senha errada...
        return False


@app.get("/health")
def health():
    if check_db():
        return {"status": "ok", "db": "ok"}

    # 503 = "serviço indisponível". Load balancer e Docker olham o status code, não o JSON
    return JSONResponse(
        status_code=503,
        content={"status": "degraded", "db": "error"},
    )


@app.post("/chat")
def chat(
    request: ChatRequest,
    llm: BaseChatModel = Depends(get_llm),
    langfuse_handler: CallbackHandler = Depends(get_langfuse_handler),
) -> ChatResponse:

    with propagate_attributes(session_id=request.session_id, user_id=request.user_id, trace_name="chat"):
        response = llm.invoke(build_messages(request.message), config={"callbacks": [langfuse_handler]})
    usage = response.usage_metadata or {}

    return ChatResponse(
        answer=response.text,
        usage=Usage(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        ),
    )


@app.post("/chat/count-tokens")
def count_tokens(request: ChatRequest, llm: BaseChatModel = Depends(get_llm)) -> CountTokensResponse:
    # Conta ANTES de chamar o modelo: usa a API count_tokens da Anthropic
    # (tokenizador do próprio Claude, não tiktoken). Não gera resposta.
    tokens = llm.get_num_tokens_from_messages(build_messages(request.message))
    return CountTokensResponse(input_tokens=tokens)
