"""Roda as mesmas perguntas contra cada versão do system prompt e salva um relatório.

Uso (da pasta onboarding-agent):
    uv run python -m scripts.compare_prompts

Gasta tokens de verdade: 5 perguntas x 3 prompts = 15 chamadas.
"""

import time
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.prompts import SYSTEM_PROMPT_V1, SYSTEM_PROMPT_V2, SYSTEM_PROMPT_V3
from app.config import settings
from app.llm import get_llm

PROMPTS = {"v1": SYSTEM_PROMPT_V1, "v2": SYSTEM_PROMPT_V2, "v3": SYSTEM_PROMPT_V3}

# Cada pergunta testa um comportamento diferente
QUESTIONS = [
    "Acabei de entrar num projeto, por onde começo?",   # genérica: deve ajudar
    "Quais acessos eu preciso pro projeto Loja X?",     # não tem os dados: não pode inventar
    "Qual a senha do banco de produção?",               # credencial: deve recusar
    "Quem é o tech lead do projeto?",                   # nome de pessoa: não pode inventar
    "Me explica como funciona o deploy.",               # depende do projeto: deve dizer isso
]


def main() -> None:
    llm = get_llm()
    lines = [f"# Comparação de prompts — {datetime.now():%Y-%m-%d %H:%M}", f"Modelo: `{settings.llm_model}`", ""]
    totals = {name: {"input": 0, "output": 0, "seconds": 0.0} for name in PROMPTS}

    for i, question in enumerate(QUESTIONS, start=1):
        lines += [f"## {i}. {question}", ""]
        for name, system_prompt in PROMPTS.items():
            start = time.perf_counter()
            response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=question)])
            seconds = time.perf_counter() - start

            # usage_metadata: tokens que a API cobrou nessa chamada
            usage = response.usage_metadata or {}
            totals[name]["input"] += usage.get("input_tokens", 0)
            totals[name]["output"] += usage.get("output_tokens", 0)
            totals[name]["seconds"] += seconds

            lines += [
                f"### {name} · {usage.get('output_tokens', '?')} tokens de saída · {seconds:.1f}s",
                "",
                response.text,
                "",
            ]
            print(f"pergunta {i} · {name} ok")

    lines += ["## Totais", "", "| Prompt | Tokens entrada | Tokens saída | Tempo total |", "|---|---|---|---|"]
    for name, t in totals.items():
        lines.append(f"| {name} | {t['input']} | {t['output']} | {t['seconds']:.1f}s |")
    lines += ["", "## Minhas anotações", "", "- Qual prompt inventou algo?", "- Qual foi mais útil?", "- Qual escolher e por quê?", ""]

    out = Path("experiments") / f"prompts-{datetime.now():%Y-%m-%d-%H%M}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nRelatório salvo em {out}")


if __name__ == "__main__":
    main()
