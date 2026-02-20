"""
Testes para o backend FastAPI do chat com Claude AI.

Este módulo testa todos os endpoints e comportamentos do sistema,
incluindo validações, janela deslizante e integração com a API do Claude.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import uuid
from datetime import datetime, timedelta

# Adicionar o diretório pai ao path para importar o módulo backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import backend.main as main_module
from backend.main import (
    app,
    SLIDING_WINDOW_SIZE,
    MAX_MESSAGE_LENGTH,
    MAX_CONCURRENT_SESSIONS,
    SESSION_INACTIVITY_TIMEOUT_MINUTES,
)


# Session ID fixo para testes
TEST_SESSION_ID = "test-session-123"


@pytest.fixture
def client():
    """
    Fixture que fornece um TestClient do FastAPI.

    Yields:
        TestClient: Cliente de teste para fazer requisições HTTP
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """
    Fixture que limpa as sessões e rate limit antes e depois de cada teste.

    Garante isolamento entre os testes, evitando que o estado de um teste
    afete outro.
    """
    main_module.sessions.clear()
    main_module.rate_limit_tracker.clear()
    yield
    main_module.sessions.clear()
    main_module.rate_limit_tracker.clear()


@pytest.fixture
def mock_anthropic_client():
    """
    Fixture que cria um mock do cliente Anthropic.

    Retorna um mock que simula a resposta da API do Claude,
    evitando chamadas reais durante os testes.

    Returns:
        Mock: Objeto mock configurado para simular respostas do Claude
    """
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Resposta do Claude")]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    return mock_client


class TestRootEndpoint:
    """Testes para o endpoint raiz GET /"""

    def test_root_returns_frontend(self, client):
        """Testa se o endpoint raiz serve o frontend (index.html)."""
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        # Verificar que é HTML válido
        html_content = response.text
        assert "<!DOCTYPE html>" in html_content
        assert "<title>Chat com Claude AI</title>" in html_content
        assert "messages-container" in html_content


class TestChatEndpoint:
    """Testes para o endpoint POST /chat"""

    @patch('backend.main.client')
    def test_chat_with_valid_message(self, mock_client, client, mock_anthropic_client):
        """Testa envio de mensagem válida."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        response = client.post("/chat", json={"message": "Olá, Claude!", "session_id": TEST_SESSION_ID})

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert "history_size" in data
        assert "session_id" in data
        assert data["response"] == "Resposta do Claude"
        assert data["history_size"] == 2  # user + assistant
        assert data["session_id"] == TEST_SESSION_ID

    def test_chat_with_empty_message(self, client):
        """Testa que mensagem vazia retorna erro de validação."""
        response = client.post("/chat", json={"message": "", "session_id": TEST_SESSION_ID})

        assert response.status_code == 422  # Unprocessable Entity

    def test_chat_with_whitespace_only_message(self, client):
        """Testa que mensagem com apenas espaços retorna erro."""
        response = client.post("/chat", json={"message": "   ", "session_id": TEST_SESSION_ID})

        assert response.status_code == 422

    def test_chat_with_message_exceeding_max_length(self, client):
        """Testa que mensagem muito longa retorna erro."""
        long_message = "a" * (MAX_MESSAGE_LENGTH + 1)
        response = client.post("/chat", json={"message": long_message, "session_id": TEST_SESSION_ID})

        assert response.status_code == 422

    def test_chat_with_max_length_message(self, client, mock_anthropic_client):
        """Testa que mensagem no limite máximo é aceita."""
        with patch('backend.main.client', mock_anthropic_client):
            max_message = "a" * MAX_MESSAGE_LENGTH
            response = client.post("/chat", json={"message": max_message, "session_id": TEST_SESSION_ID})

            assert response.status_code == 200

    @patch('backend.main.client')
    def test_chat_trims_whitespace(self, mock_client, client, mock_anthropic_client):
        """Testa que espaços nas pontas da mensagem são removidos."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        response = client.post("/chat", json={"message": "  Olá!  ", "session_id": TEST_SESSION_ID})

        assert response.status_code == 200
        # Verificar se a mensagem foi adicionada ao histórico sem espaços
        assert main_module.sessions[TEST_SESSION_ID]["history"][0]["content"] == "Olá!"

    @patch('backend.main.client')
    def test_chat_adds_messages_to_history(self, mock_client, client, mock_anthropic_client):
        """Testa que mensagens são adicionadas ao histórico corretamente."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        client.post("/chat", json={"message": "Primeira mensagem", "session_id": TEST_SESSION_ID})

        history = main_module.sessions[TEST_SESSION_ID]["history"]
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Primeira mensagem"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Resposta do Claude"

    @patch('backend.main.client')
    def test_chat_sliding_window_applies_correctly(self, mock_client, client, mock_anthropic_client):
        """Testa que a janela deslizante limita o envio ao máximo de SLIDING_WINDOW_SIZE mensagens."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Pré-popular histórico com SLIDING_WINDOW_SIZE mensagens (10 turnos completos)
        # sem passar pelo endpoint, evitando interferência do rate limit
        history = []
        for i in range(SLIDING_WINDOW_SIZE // 2):
            history.append({"role": "user", "content": f"Mensagem {i+1}"})
            history.append({"role": "assistant", "content": f"Resposta {i+1}"})
        main_module.sessions[TEST_SESSION_ID] = {"history": history, "last_activity": datetime.now()}
        assert len(main_module.sessions[TEST_SESSION_ID]["history"]) == SLIDING_WINDOW_SIZE

        # Enviar a próxima mensagem via endpoint — deve acionar a janela (21 > 20)
        response = client.post("/chat", json={"message": "Mensagem 11", "session_id": TEST_SESSION_ID})
        assert response.status_code == 200

        # Histórico deve ter SLIDING_WINDOW_SIZE + 2 entradas (user + assistant adicionados)
        assert len(main_module.sessions[TEST_SESSION_ID]["history"]) == SLIDING_WINDOW_SIZE + 2

        # Apenas SLIDING_WINDOW_SIZE mensagens foram enviadas à API (janela aplicada como slice)
        messages_sent = mock_client.messages.create.call_args.kwargs['messages']
        assert len(messages_sent) == SLIDING_WINDOW_SIZE

    @patch('backend.main.client')
    def test_chat_api_error_returns_500(self, mock_client, client):
        """Testa que erro da API do Claude retorna HTTP 500."""
        mock_client.messages.create.side_effect = Exception("API Error")

        response = client.post("/chat", json={"message": "Teste", "session_id": TEST_SESSION_ID})

        assert response.status_code == 500
        assert "Erro ao processar mensagem" in response.json()["detail"]


class TestClearEndpoint:
    """Testes para o endpoint POST /clear"""

    @patch('backend.main.client')
    def test_clear_removes_all_history(self, mock_client, client, mock_anthropic_client):
        """Testa que clear remove todo o histórico."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Adicionar algumas mensagens
        client.post("/chat", json={"message": "Mensagem 1", "session_id": TEST_SESSION_ID})
        client.post("/chat", json={"message": "Mensagem 2", "session_id": TEST_SESSION_ID})

        history = main_module.sessions[TEST_SESSION_ID]["history"]
        assert len(history) > 0

        # Limpar histórico
        response = client.post("/clear", json={"session_id": TEST_SESSION_ID})

        assert response.status_code == 200
        assert response.json()["message"] == "Histórico limpo com sucesso"
        assert len(main_module.sessions[TEST_SESSION_ID]["history"]) == 0

    def test_clear_on_nonexistent_session(self, client):
        """Testa que clear retorna 404 para sessão inexistente."""
        response = client.post("/clear", json={"session_id": "nonexistent-session"})

        assert response.status_code == 404


class TestHistoryEndpoint:
    """Testes para o endpoint GET /history/{session_id}"""

    @patch('backend.main.client')
    def test_history_on_new_session(self, mock_client, client, mock_anthropic_client):
        """Testa que history retorna 404 para sessão inexistente."""
        response = client.get(f"/history/{TEST_SESSION_ID}")

        assert response.status_code == 404

    @patch('backend.main.client')
    def test_history_returns_all_messages(self, mock_client, client, mock_anthropic_client):
        """Testa que history retorna todas as mensagens, não apenas a janela."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Adicionar mensagens
        client.post("/chat", json={"message": "Mensagem 1", "session_id": TEST_SESSION_ID})
        client.post("/chat", json={"message": "Mensagem 2", "session_id": TEST_SESSION_ID})

        response = client.get(f"/history/{TEST_SESSION_ID}")
        data = response.json()

        assert response.status_code == 200
        assert data["total_messages"] == 4  # 2 user + 2 assistant
        assert data["window_size"] == SLIDING_WINDOW_SIZE
        assert len(data["history"]) == 4

        # Verificar estrutura das mensagens
        assert data["history"][0]["role"] == "user"
        assert data["history"][0]["content"] == "Mensagem 1"
        assert data["history"][1]["role"] == "assistant"
        assert data["history"][2]["role"] == "user"
        assert data["history"][2]["content"] == "Mensagem 2"
        assert data["history"][3]["role"] == "assistant"

    @patch('backend.main.client')
    def test_history_shows_all_even_beyond_sliding_window(self, mock_client, client, mock_anthropic_client):
        """Testa que history mostra todas as mensagens, mesmo além da janela."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Adicionar 5 mensagens (10 no total)
        for i in range(5):
            client.post("/chat", json={"message": f"Mensagem {i+1}", "session_id": TEST_SESSION_ID})

        response = client.get(f"/history/{TEST_SESSION_ID}")
        data = response.json()

        assert data["total_messages"] == 10
        assert len(data["history"]) == 10
        # Mesmo que a janela seja 6, o histórico completo deve ter todas


class TestChatRequestValidation:
    """Testes para validação do modelo ChatRequest"""

    def test_missing_message_field(self, client):
        """Testa que requisição sem campo 'message' retorna erro."""
        response = client.post("/chat", json={})

        assert response.status_code == 422

    def test_null_message(self, client):
        """Testa que mensagem null retorna erro."""
        response = client.post("/chat", json={"message": None})

        assert response.status_code == 422

    def test_invalid_json(self, client):
        """Testa que JSON inválido retorna erro."""
        response = client.post(
            "/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422


class TestSlidingWindowBehavior:
    """Testes específicos para o comportamento da janela deslizante"""

    @patch('backend.main.client')
    def test_sliding_window_with_exactly_window_size_messages(self, mock_client, client, mock_anthropic_client):
        """Testa comportamento quando histórico tem exatamente SLIDING_WINDOW_SIZE mensagens."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Adicionar 10 turnos (20 mensagens = exatamente SLIDING_WINDOW_SIZE)
        for i in range(10):
            client.post("/chat", json={"message": f"Mensagem {i+1}", "session_id": TEST_SESSION_ID})

        history = main_module.sessions[TEST_SESSION_ID]["history"]
        assert len(history) == SLIDING_WINDOW_SIZE

        # Próxima mensagem deve acionar a janela deslizante (21 > 20)
        client.post("/chat", json={"message": "Mensagem 11", "session_id": TEST_SESSION_ID})

        call_args = mock_client.messages.create.call_args
        messages_sent = call_args.kwargs['messages']

        # Deve enviar exatamente SLIDING_WINDOW_SIZE mensagens
        assert len(messages_sent) == SLIDING_WINDOW_SIZE

    @patch('backend.main.client')
    def test_sliding_window_discards_old_messages(self, mock_client, client, mock_anthropic_client):
        """Testa que janela deslizante descarta mensagens antigas quando histórico excede o limite."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Pré-popular com SLIDING_WINDOW_SIZE + 2 mensagens (11 turnos = 22 entradas)
        # sem passar pelo endpoint, evitando interferência do rate limit
        history = []
        for i in range(SLIDING_WINDOW_SIZE // 2 + 1):
            history.append({"role": "user", "content": f"Mensagem {i+1}"})
            history.append({"role": "assistant", "content": f"Resposta {i+1}"})
        main_module.sessions[TEST_SESSION_ID] = {"history": history, "last_activity": datetime.now()}
        assert len(main_module.sessions[TEST_SESSION_ID]["history"]) == SLIDING_WINDOW_SIZE + 2

        # Enviar mais uma mensagem via endpoint — janela obrigatoriamente aplicada (23 > 20)
        response = client.post("/chat", json={"message": "Mensagem nova", "session_id": TEST_SESSION_ID})
        assert response.status_code == 200

        # Histórico completo cresce normalmente
        assert len(main_module.sessions[TEST_SESSION_ID]["history"]) == SLIDING_WINDOW_SIZE + 4

        # Apenas SLIDING_WINDOW_SIZE mensagens foram enviadas à API (janela aplicada como slice)
        messages_sent = mock_client.messages.create.call_args.kwargs['messages']
        assert len(messages_sent) == SLIDING_WINDOW_SIZE

        # A última mensagem na janela é a última enviada pelo usuário
        assert messages_sent[-1]["content"] == "Mensagem nova"


class TestRateLimiting:
    """Testes para o rate limiting"""

    @patch('backend.main.client')
    def test_rate_limit_allows_requests_under_limit(self, mock_client, client, mock_anthropic_client):
        """Testa que requisições dentro do limite são permitidas."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Enviar algumas requisições (menos que o limite)
        for i in range(5):
            response = client.post("/chat", json={"message": f"Mensagem {i+1}", "session_id": TEST_SESSION_ID})
            assert response.status_code == 200

    @patch('backend.main.client')
    def test_rate_limit_blocks_excessive_requests(self, mock_client, client, mock_anthropic_client):
        """Testa que requisições excessivas são bloqueadas com HTTP 429."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Enviar requisições até exceder o limite (10 requisições por minuto)
        for i in range(main_module.RATE_LIMIT_MAX_REQUESTS):
            response = client.post("/chat", json={"message": f"Mensagem {i+1}", "session_id": TEST_SESSION_ID})
            assert response.status_code == 200

        # A próxima requisição deve ser bloqueada
        response = client.post("/chat", json={"message": "Mensagem extra", "session_id": TEST_SESSION_ID})
        assert response.status_code == 429
        assert "Limite de requisições excedido" in response.json()["detail"]

    @patch('backend.main.client')
    def test_rate_limit_per_session(self, mock_client, client, mock_anthropic_client):
        """Testa que rate limit é aplicado por sessão."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        session_a = "session-a"
        session_b = "session-b"

        # Esgotar limite da sessão A
        for i in range(main_module.RATE_LIMIT_MAX_REQUESTS):
            response = client.post("/chat", json={"message": f"Mensagem {i+1}", "session_id": session_a})
            assert response.status_code == 200

        # Sessão A está bloqueada
        response = client.post("/chat", json={"message": "Bloqueada", "session_id": session_a})
        assert response.status_code == 429

        # Sessão B ainda pode enviar
        response = client.post("/chat", json={"message": "Permitida", "session_id": session_b})
        assert response.status_code == 200


class TestSessionIsolation:
    """Testes para isolamento de sessões"""

    @patch('backend.main.client')
    def test_sessions_are_isolated(self, mock_client, client, mock_anthropic_client):
        """Testa que sessões diferentes têm históricos separados."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        session_a = "session-a"
        session_b = "session-b"

        # Enviar mensagem na sessão A
        client.post("/chat", json={"message": "Mensagem A", "session_id": session_a})

        # Enviar mensagem na sessão B
        client.post("/chat", json={"message": "Mensagem B", "session_id": session_b})

        # Verificar isolamento
        history_a = main_module.sessions[session_a]["history"]
        history_b = main_module.sessions[session_b]["history"]

        assert history_a[0]["content"] == "Mensagem A"
        assert history_b[0]["content"] == "Mensagem B"
        assert len(history_a) == 2
        assert len(history_b) == 2


class TestIntegration:
    """Testes de integração para fluxos completos"""

    @patch('backend.main.client')
    def test_complete_conversation_flow(self, mock_client, client, mock_anthropic_client):
        """Testa fluxo completo: chat, verificar histórico, limpar."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # 1. Enviar mensagem
        response1 = client.post("/chat", json={"message": "Olá", "session_id": TEST_SESSION_ID})
        assert response1.status_code == 200
        assert response1.json()["history_size"] == 2

        # 2. Verificar histórico
        history_response = client.get(f"/history/{TEST_SESSION_ID}")
        assert history_response.json()["total_messages"] == 2

        # 3. Enviar outra mensagem
        response2 = client.post("/chat", json={"message": "Como você está?", "session_id": TEST_SESSION_ID})
        assert response2.status_code == 200
        assert response2.json()["history_size"] == 4

        # 4. Limpar histórico
        clear_response = client.post("/clear", json={"session_id": TEST_SESSION_ID})
        assert clear_response.status_code == 200

        # 5. Verificar que histórico está vazio
        final_history = client.get(f"/history/{TEST_SESSION_ID}")
        assert final_history.json()["total_messages"] == 0


class TestSessionLimit:
    """Testes para limitação de sessões simultâneas (máx. 4) com expiração por inatividade."""

    def _add_session(self, session_id: str = None, minutes_inactive: int = 0) -> str:
        """Helper: injeta uma sessão diretamente no estado do servidor."""
        sid = session_id or str(uuid.uuid4())
        main_module.sessions[sid] = {
            "history": [],
            "last_activity": datetime.now() - timedelta(minutes=minutes_inactive),
        }
        return sid

    def test_blocks_fifth_session(self, client):
        """5ª sessão nova deve ser bloqueada com HTTP 503."""
        for _ in range(MAX_CONCURRENT_SESSIONS):
            self._add_session()

        response = client.post("/chat", json={"message": "oi"})

        assert response.status_code == 503

    def test_error_message_at_limit(self, client):
        """Mensagem de erro ao atingir o limite deve corresponder ao texto especificado."""
        for _ in range(MAX_CONCURRENT_SESSIONS):
            self._add_session()

        response = client.post("/chat", json={"message": "oi"})
        detail = response.json()["detail"]

        assert "Limite de usuários atingido" in detail
        assert "Tente novamente mais tarde" in detail

    def test_claude_api_not_called_when_limit_reached(self, client):
        """API Claude não deve ser chamada quando o limite de sessões é atingido."""
        for _ in range(MAX_CONCURRENT_SESSIONS):
            self._add_session()

        with patch("backend.main.client") as mock_client:
            client.post("/chat", json={"message": "oi"})
            mock_client.messages.create.assert_not_called()

    def test_existing_session_allowed_when_at_limit(self, client, mock_anthropic_client):
        """Sessão já existente deve continuar funcionando mesmo com o limite atingido."""
        existing_sid = self._add_session()
        for _ in range(MAX_CONCURRENT_SESSIONS - 1):
            self._add_session()

        with patch("backend.main.client") as mock_client:
            mock_client.messages.create = mock_anthropic_client.messages.create
            response = client.post(
                "/chat",
                json={"message": "continuo aqui", "session_id": existing_sid},
            )

        assert response.status_code == 200

    def test_inactive_session_releases_slot(self, client, mock_anthropic_client):
        """Sessão inativa há mais de 5 min deve ser removida e liberar vaga para nova sessão."""
        # 1 inativa (vai ser removida pelo cleanup)
        self._add_session(minutes_inactive=SESSION_INACTIVITY_TIMEOUT_MINUTES + 1)
        # 3 ativas => total de 4 (limite atingido antes do cleanup)
        for _ in range(MAX_CONCURRENT_SESSIONS - 1):
            self._add_session()

        with patch("backend.main.client") as mock_client:
            mock_client.messages.create = mock_anthropic_client.messages.create
            response = client.post("/chat", json={"message": "oi"})

        assert response.status_code == 200

    def test_cleanup_removes_only_inactive_sessions(self, client):
        """cleanup_inactive_sessions deve remover apenas sessões expiradas, preservando as ativas."""
        active_sid = self._add_session()
        inactive_sid = self._add_session(
            minutes_inactive=SESSION_INACTIVITY_TIMEOUT_MINUTES + 1
        )

        removed = main_module.cleanup_inactive_sessions()

        assert removed == 1
        assert active_sid in main_module.sessions
        assert inactive_sid not in main_module.sessions

    def test_max_four_sessions_allowed(self, client, mock_anthropic_client):
        """Exatamente 4 sessões simultâneas devem ser aceitas."""
        with patch("backend.main.client") as mock_client:
            mock_client.messages.create = mock_anthropic_client.messages.create
            for i in range(MAX_CONCURRENT_SESSIONS):
                response = client.post("/chat", json={"message": f"sessão {i + 1}"})
                assert response.status_code == 200

        assert len(main_module.sessions) == MAX_CONCURRENT_SESSIONS

    def test_session_limit_constant_is_four(self):
        """Constante MAX_CONCURRENT_SESSIONS deve ser 4."""
        assert MAX_CONCURRENT_SESSIONS == 4

    def test_inactivity_timeout_constant_is_five_minutes(self):
        """Constante SESSION_INACTIVITY_TIMEOUT_MINUTES deve ser 5."""
        assert SESSION_INACTIVITY_TIMEOUT_MINUTES == 5
