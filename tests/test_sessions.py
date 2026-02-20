"""
Testes para o sistema de sessões isoladas.

Verifica se cada usuário possui seu próprio histórico de conversas,
garantindo que não há compartilhamento de estado global.
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_multiple_sessions_are_isolated():
    """
    Testa se múltiplas sessões são completamente isoladas.

    Cenário:
        - Usuário A envia mensagem na sessão A
        - Usuário B envia mensagem na sessão B
        - Verificar que cada sessão tem apenas suas próprias mensagens
    """
    # Sessão A - Primeira mensagem
    response_a1 = client.post("/chat", json={
        "message": "Olá, meu nome é Alice"
    })
    assert response_a1.status_code == 200
    data_a1 = response_a1.json()
    session_a = data_a1["session_id"]
    assert data_a1["history_size"] == 2  # user + assistant

    # Sessão B - Primeira mensagem (diferente da sessão A)
    response_b1 = client.post("/chat", json={
        "message": "Oi, meu nome é Bob"
    })
    assert response_b1.status_code == 200
    data_b1 = response_b1.json()
    session_b = data_b1["session_id"]
    assert data_b1["history_size"] == 2  # user + assistant

    # Verificar que sessions são diferentes
    assert session_a != session_b

    # Sessão A - Segunda mensagem
    response_a2 = client.post("/chat", json={
        "message": "Qual é o meu nome?",
        "session_id": session_a
    })
    assert response_a2.status_code == 200
    data_a2 = response_a2.json()
    assert data_a2["session_id"] == session_a
    assert data_a2["history_size"] == 4  # 2 anteriores + 2 novas

    # Sessão B - Segunda mensagem
    response_b2 = client.post("/chat", json={
        "message": "Qual é o meu nome?",
        "session_id": session_b
    })
    assert response_b2.status_code == 200
    data_b2 = response_b2.json()
    assert data_b2["session_id"] == session_b
    assert data_b2["history_size"] == 4  # 2 anteriores + 2 novas

    # Verificar histórico da sessão A
    history_a = client.get(f"/history/{session_a}")
    assert history_a.status_code == 200
    history_a_data = history_a.json()
    assert history_a_data["total_messages"] == 4
    assert "Alice" in history_a_data["history"][0]["content"]

    # Verificar histórico da sessão B
    history_b = client.get(f"/history/{session_b}")
    assert history_b.status_code == 200
    history_b_data = history_b.json()
    assert history_b_data["total_messages"] == 4
    assert "Bob" in history_b_data["history"][0]["content"]

    print("[OK] Teste de isolamento de sessoes passou!")


def test_session_persistence():
    """
    Testa se a sessão persiste entre requisições quando session_id é fornecido.
    """
    # Primeira mensagem - criar sessão
    response1 = client.post("/chat", json={
        "message": "Lembre-se: minha cor favorita é azul"
    })
    assert response1.status_code == 200
    data1 = response1.json()
    session_id = data1["session_id"]

    # Segunda mensagem - usar mesma sessão
    response2 = client.post("/chat", json={
        "message": "Qual é minha cor favorita?",
        "session_id": session_id
    })
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["session_id"] == session_id
    assert data2["history_size"] == 4  # 2 + 2

    # Verificar que o histórico foi mantido
    history = client.get(f"/history/{session_id}")
    assert history.status_code == 200
    history_data = history.json()
    assert history_data["total_messages"] == 4
    assert "azul" in history_data["history"][0]["content"]

    print("[OK] Teste de persistencia de sessao passou!")


def test_clear_session():
    """
    Testa se limpar uma sessão não afeta outras sessões.
    """
    # Criar sessão A
    response_a = client.post("/chat", json={
        "message": "Sessao A"
    })
    session_a = response_a.json()["session_id"]

    # Criar sessão B
    response_b = client.post("/chat", json={
        "message": "Sessao B"
    })
    session_b = response_b.json()["session_id"]

    # Limpar apenas sessão A
    clear_response = client.post("/clear", json={
        "session_id": session_a
    })
    assert clear_response.status_code == 200

    # Verificar que sessão A foi limpa
    history_a = client.get(f"/history/{session_a}")
    assert history_a.status_code == 200
    assert history_a.json()["total_messages"] == 0

    # Verificar que sessão B não foi afetada
    history_b = client.get(f"/history/{session_b}")
    assert history_b.status_code == 200
    assert history_b.json()["total_messages"] == 2

    print("[OK] Teste de limpeza de sessao isolada passou!")


def test_session_not_found():
    """
    Testa o comportamento quando uma sessão inexistente é consultada.
    """
    fake_session_id = "fake-session-id-12345"

    # Tentar obter histórico de sessão inexistente
    response = client.get(f"/history/{fake_session_id}")
    assert response.status_code == 404
    detail = response.json()["detail"].lower()
    assert "encontrada" in detail or "not found" in detail

    # Tentar limpar sessão inexistente
    clear_response = client.post("/clear", json={
        "session_id": fake_session_id
    })
    assert clear_response.status_code == 404

    print("[OK] Teste de sessao nao encontrada passou!")


def test_list_sessions():
    """
    Testa o endpoint de listagem de sessões.
    """
    # Criar algumas sessões
    response1 = client.post("/chat", json={"message": "Teste 1"})
    session1 = response1.json()["session_id"]

    response2 = client.post("/chat", json={"message": "Teste 2"})
    session2 = response2.json()["session_id"]

    # Listar sessões
    sessions_response = client.get("/sessions")
    assert sessions_response.status_code == 200
    data = sessions_response.json()

    assert data["total_sessions"] >= 2
    session_ids = [s["session_id"] for s in data["sessions"]]
    assert session1 in session_ids
    assert session2 in session_ids

    print("[OK] Teste de listagem de sessoes passou!")


if __name__ == "__main__":
    print("\n========================================")
    print("Executando testes de sistema de sessoes")
    print("========================================\n")

    test_multiple_sessions_are_isolated()
    test_session_persistence()
    test_clear_session()
    test_session_not_found()
    test_list_sessions()

    print("\n========================================")
    print("Todos os testes passaram com sucesso!")
    print("========================================")
