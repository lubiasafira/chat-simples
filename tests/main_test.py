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

# Adicionar o diretório pai ao path para importar o módulo backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import backend.main as main_module
from backend.main import app, SLIDING_WINDOW_SIZE, MAX_MESSAGE_LENGTH


@pytest.fixture
def client():
    """
    Fixture que fornece um TestClient do FastAPI.

    Yields:
        TestClient: Cliente de teste para fazer requisições HTTP
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_conversation_history():
    """
    Fixture que limpa o histórico de conversas antes e depois de cada teste.

    Garante isolamento entre os testes, evitando que o estado de um teste
    afete outro.
    """
    main_module.conversation_history.clear()
    yield
    main_module.conversation_history.clear()


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

        response = client.post("/chat", json={"message": "Olá, Claude!"})

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert "history_size" in data
        assert data["response"] == "Resposta do Claude"
        assert data["history_size"] == 2  # user + assistant

    def test_chat_with_empty_message(self, client):
        """Testa que mensagem vazia retorna erro de validação."""
        response = client.post("/chat", json={"message": ""})

        assert response.status_code == 422  # Unprocessable Entity

    def test_chat_with_whitespace_only_message(self, client):
        """Testa que mensagem com apenas espaços retorna erro."""
        response = client.post("/chat", json={"message": "   "})

        assert response.status_code == 422

    def test_chat_with_message_exceeding_max_length(self, client):
        """Testa que mensagem muito longa retorna erro."""
        long_message = "a" * (MAX_MESSAGE_LENGTH + 1)
        response = client.post("/chat", json={"message": long_message})

        assert response.status_code == 422

    def test_chat_with_max_length_message(self, client, mock_anthropic_client):
        """Testa que mensagem no limite máximo é aceita."""
        with patch('backend.main.client', mock_anthropic_client):
            max_message = "a" * MAX_MESSAGE_LENGTH
            response = client.post("/chat", json={"message": max_message})

            assert response.status_code == 200

    @patch('backend.main.client')
    def test_chat_trims_whitespace(self, mock_client, client, mock_anthropic_client):
        """Testa que espaços nas pontas da mensagem são removidos."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        response = client.post("/chat", json={"message": "  Olá!  "})

        assert response.status_code == 200
        # Verificar se a mensagem foi adicionada ao histórico sem espaços
        assert main_module.conversation_history[0]["content"] == "Olá!"

    @patch('backend.main.client')
    def test_chat_adds_messages_to_history(self, mock_client, client, mock_anthropic_client):
        """Testa que mensagens são adicionadas ao histórico corretamente."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        client.post("/chat", json={"message": "Primeira mensagem"})

        assert len(main_module.conversation_history) == 2
        assert main_module.conversation_history[0]["role"] == "user"
        assert main_module.conversation_history[0]["content"] == "Primeira mensagem"
        assert main_module.conversation_history[1]["role"] == "assistant"
        assert main_module.conversation_history[1]["content"] == "Resposta do Claude"

    @patch('backend.main.client')
    def test_chat_sliding_window_applies_correctly(self, mock_client, client, mock_anthropic_client):
        """Testa que a janela deslizante mantém apenas as últimas 6 mensagens."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Enviar 5 mensagens (cada uma adiciona 2: user + assistant = 10 no total)
        for i in range(5):
            client.post("/chat", json={"message": f"Mensagem {i+1}"})

        # Verificar que temos 10 mensagens no histórico
        assert len(main_module.conversation_history) == 10

        # Fazer mais uma requisição e verificar que apenas as últimas 6 são enviadas
        response = client.post("/chat", json={"message": "Mensagem 6"})

        # Verificar que o histórico completo tem 12 mensagens
        assert len(main_module.conversation_history) == 12

        # Verificar que apenas as últimas 6 mensagens foram enviadas para a API
        # (a janela deslizante deve ter pegado as últimas 6 antes de adicionar a nova)
        call_args = mock_client.messages.create.call_args
        messages_sent = call_args.kwargs['messages']

        assert len(messages_sent) == SLIDING_WINDOW_SIZE

    @patch('backend.main.client')
    def test_chat_api_error_returns_500(self, mock_client, client):
        """Testa que erro da API do Claude retorna HTTP 500."""
        mock_client.messages.create.side_effect = Exception("API Error")

        response = client.post("/chat", json={"message": "Teste"})

        assert response.status_code == 500
        assert "Erro ao processar mensagem" in response.json()["detail"]


class TestClearEndpoint:
    """Testes para o endpoint POST /clear"""

    @patch('backend.main.client')
    def test_clear_removes_all_history(self, mock_client, client, mock_anthropic_client):
        """Testa que clear remove todo o histórico."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Adicionar algumas mensagens
        client.post("/chat", json={"message": "Mensagem 1"})
        client.post("/chat", json={"message": "Mensagem 2"})

        assert len(main_module.conversation_history) > 0

        # Limpar histórico
        response = client.post("/clear")

        assert response.status_code == 200
        assert response.json()["message"] == "Histórico limpo com sucesso"
        assert len(main_module.conversation_history) == 0

    def test_clear_on_empty_history(self, client):
        """Testa que clear funciona mesmo com histórico vazio."""
        response = client.post("/clear")

        assert response.status_code == 200
        assert len(main_module.conversation_history) == 0


class TestHistoryEndpoint:
    """Testes para o endpoint GET /history"""

    def test_history_on_empty_conversation(self, client):
        """Testa que history retorna estrutura correta com histórico vazio."""
        response = client.get("/history")

        assert response.status_code == 200
        data = response.json()

        assert data["total_messages"] == 0
        assert data["window_size"] == SLIDING_WINDOW_SIZE
        assert data["history"] == []

    @patch('backend.main.client')
    def test_history_returns_all_messages(self, mock_client, client, mock_anthropic_client):
        """Testa que history retorna todas as mensagens, não apenas a janela."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Adicionar mensagens
        client.post("/chat", json={"message": "Mensagem 1"})
        client.post("/chat", json={"message": "Mensagem 2"})

        response = client.get("/history")
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
            client.post("/chat", json={"message": f"Mensagem {i+1}"})

        response = client.get("/history")
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
    def test_sliding_window_with_exactly_6_messages(self, mock_client, client, mock_anthropic_client):
        """Testa comportamento quando histórico tem exatamente 6 mensagens."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Adicionar 3 turnos (6 mensagens)
        for i in range(3):
            client.post("/chat", json={"message": f"Mensagem {i+1}"})

        assert len(main_module.conversation_history) == 6

        # Próxima mensagem deve usar janela deslizante
        client.post("/chat", json={"message": "Mensagem 4"})

        call_args = mock_client.messages.create.call_args
        messages_sent = call_args.kwargs['messages']

        # Deve enviar as últimas 6 do histórico de 6 (todas elas)
        assert len(messages_sent) == 6

    @patch('backend.main.client')
    def test_sliding_window_discards_old_messages(self, mock_client, client, mock_anthropic_client):
        """Testa que janela deslizante descarta mensagens antigas."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # Adicionar muitas mensagens
        for i in range(10):
            client.post("/chat", json={"message": f"Mensagem {i+1}"})

        # Histórico deve ter todas as 20 mensagens
        assert len(main_module.conversation_history) == 20

        # Mas apenas as últimas 6 devem ser enviadas
        call_args = mock_client.messages.create.call_args
        messages_sent = call_args.kwargs['messages']

        assert len(messages_sent) == SLIDING_WINDOW_SIZE

        # Verificar que são as mensagens mais recentes
        # A última mensagem do usuário na janela deve ser "Mensagem 10"
        # (pois ela é adicionada ao histórico antes da janela deslizante ser aplicada)
        assert messages_sent[-1]["content"] == "Mensagem 10"


class TestIntegration:
    """Testes de integração para fluxos completos"""

    @patch('backend.main.client')
    def test_complete_conversation_flow(self, mock_client, client, mock_anthropic_client):
        """Testa fluxo completo: chat, verificar histórico, limpar."""
        mock_client.messages.create = mock_anthropic_client.messages.create

        # 1. Enviar mensagem
        response1 = client.post("/chat", json={"message": "Olá"})
        assert response1.status_code == 200
        assert response1.json()["history_size"] == 2

        # 2. Verificar histórico
        history_response = client.get("/history")
        assert history_response.json()["total_messages"] == 2

        # 3. Enviar outra mensagem
        response2 = client.post("/chat", json={"message": "Como você está?"})
        assert response2.status_code == 200
        assert response2.json()["history_size"] == 4

        # 4. Limpar histórico
        clear_response = client.post("/clear")
        assert clear_response.status_code == 200

        # 5. Verificar que histórico está vazio
        final_history = client.get("/history")
        assert final_history.json()["total_messages"] == 0
