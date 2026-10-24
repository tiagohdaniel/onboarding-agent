from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env")

    database_url: str

    # SecretStr: se alguém der print(settings), a chave aparece como '**********'
    anthropic_api_key: SecretStr = SecretStr("")
    llm_model: str = "claude-opus-5-5"

    # Langfuse (Fase 2). Sem public key (ex: nos testes), o tracing fica desligado.
    langfuse_public_key: str = ""
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_base_url: str = "https://us.cloud.langfuse.com"


settings = Settings()
