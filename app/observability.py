from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langfuse.span_filter import is_langfuse_span

from app.config import settings

# Cria o cliente uma vez, quando o módulo é importado. Ele fica guardado dentro do
# pacote langfuse, e o CallbackHandler() lá embaixo reaproveita esse mesmo cliente.
# Os traces não saem na hora: vão num lote em segundo plano (a cada ~5s).
Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key.get_secret_value(),
    base_url=settings.langfuse_base_url,
    tracing_enabled=bool(settings.langfuse_public_key),
    # O SDK da Anthropic também gera spans (OpenTelemetry) por conta própria, e o Langfuse
    # exportaria os dois: cada chamada apareceria duplicada e com custo em dobro.
    # Aqui só sai o que o próprio Langfuse criou (os spans do CallbackHandler).
    should_export_span=is_langfuse_span,
)


def get_langfuse_handler() -> CallbackHandler:
    """Callback do LangChain: a cada chamada do LLM, ele registra um trace no Langfuse
    (prompt, resposta, tokens, custo e latência), sem mudar a chamada em si."""
    return CallbackHandler()
