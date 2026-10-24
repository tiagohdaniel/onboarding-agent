from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from app.config import settings


def get_llm() -> BaseChatModel:
    """Único lugar que sabe qual provider usamos.

    O resto do código só conhece BaseChatModel (a interface do LangChain).
    Trocar para OpenAI ou Bedrock = mudar só esta função.
    """
    return ChatAnthropic(
        model=settings.llm_model,
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
        timeout=60,
    )
