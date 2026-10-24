from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.api import app
from app.llm import get_llm

client = TestClient(app)


class FakeLLM(GenericFakeChatModel):
    # O modelo falso padrão não sabe contar tokens do Claude; aqui fingimos um número fixo
    def get_num_tokens_from_messages(self, messages, tools=None, **kwargs) -> int:
        return 42


def fake_llm():
    # Modelo falso do próprio LangChain: devolve respostas prontas, sem chamar API nem gastar token
    message = AIMessage(
        content="Fale com o tech lead.",
        usage_metadata={"input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
    )
    return FakeLLM(messages=iter([message]))


def test_chat_devolve_resposta_e_tokens():
    # dependency_overrides: "quando alguém pedir get_llm, entregue fake_llm"
    app.dependency_overrides[get_llm] = fake_llm
    try:
        response = client.post("/chat", json={"message": "Quais acessos eu preciso?"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Fale com o tech lead.",
        "usage": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
    }


def test_chat_recusa_mensagem_vazia():
    # Nem chega no LLM: o Pydantic barra antes
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_count_tokens_conta_sem_gerar_resposta():
    app.dependency_overrides[get_llm] = fake_llm
    try:
        response = client.post("/chat/count-tokens", json={"message": "oi"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"input_tokens": 42}
