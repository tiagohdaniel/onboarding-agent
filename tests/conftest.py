import os

# O pytest carrega este arquivo antes dos testes (e antes de importar o app).
# Variável de ambiente de verdade vence o .env, então aqui o tracing fica desligado:
# teste não manda trace falso para o Langfuse.
os.environ["LANGFUSE_PUBLIC_KEY"] = ""
