from fastapi.testclient import TestClient

from app import api

client = TestClient(api.app)


def test_health_ok_quando_banco_responde(monkeypatch):
    # Troca o check_db de verdade por um falso: o teste não depende do Postgres ligado
    monkeypatch.setattr(api, "check_db", lambda: True)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_503_quando_banco_fora(monkeypatch):
    monkeypatch.setattr(api, "check_db", lambda: False)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "db": "error"}
