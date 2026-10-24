# Imagem de desenvolvimento (a versão de produção vem na Fase 7)
FROM python:3.12-slim

# Copia o binário do uv de uma imagem oficial, sem precisar instalar via pip
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv

WORKDIR /app

# Primeiro só os arquivos de dependência: se o código mudar e as dependências não,
# o Docker reaproveita esta camada do cache e o build fica rápido
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

# Coloca o venv criado pelo uv no PATH, para "uvicorn" e "pytest" funcionarem direto
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
