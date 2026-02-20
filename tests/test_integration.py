"""
Testes de integração para validar o fluxo completo da aplicação.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import time

API_URL = "http://localhost:8000"

def test_complete_flow():
    """Testa o fluxo completo: envio de mensagem e recebimento de resposta."""
    print("🧪 TESTE 1: Fluxo Completo de Mensagens")
    print("-" * 50)

    # Limpar histórico antes de começar
    print("\n1. Limpando histórico...")
    response = requests.post(f"{API_URL}/clear")
    assert response.status_code == 200, f"Erro ao limpar histórico: {response.status_code}"
    print("   ✅ Histórico limpo com sucesso")

    # Enviar mensagem de teste
    print("\n2. Enviando mensagem de teste...")
    test_message = "Olá! Qual é o resultado de 2 + 2?"

    response = requests.post(
        f"{API_URL}/chat",
        json={"message": test_message}
    )

    assert response.status_code == 200, f"Erro ao enviar mensagem: {response.status_code}"
    data = response.json()

    print(f"   📤 Mensagem enviada: {test_message}")
    print(f"   📥 Resposta recebida: {data['response'][:100]}...")
    print(f"   📊 Tamanho do histórico: {data['history_size']} mensagens")

    # Validações
    assert "response" in data, "Resposta não contém campo 'response'"
    assert "history_size" in data, "Resposta não contém campo 'history_size'"
    assert len(data["response"]) > 0, "Resposta está vazia"
    assert data["history_size"] == 2, f"Histórico deveria ter 2 mensagens, mas tem {data['history_size']}"

    print("   ✅ Resposta validada com sucesso")

    # Verificar histórico
    print("\n3. Verificando histórico completo...")
    response = requests.get(f"{API_URL}/history")
    assert response.status_code == 200

    history_data = response.json()
    print(f"   📜 Total de mensagens no histórico: {history_data['total_messages']}")
    print(f"   🪟 Tamanho da janela deslizante: {history_data['window_size']}")

    assert history_data['total_messages'] == 2, "Histórico deveria ter 2 mensagens"
    assert history_data['history'][0]['role'] == 'user', "Primeira mensagem deveria ser do usuário"
    assert history_data['history'][1]['role'] == 'assistant', "Segunda mensagem deveria ser do assistente"

    print("   ✅ Histórico validado com sucesso")

    print("\n" + "="*50)
    print("✅ TESTE 1 PASSOU - Fluxo completo funcionando!")
    print("="*50 + "\n")

    return data

if __name__ == "__main__":
    try:
        print("\n🚀 Iniciando testes de integração...\n")
        test_complete_flow()
        print("\n🎉 Todos os testes passaram com sucesso!\n")
    except AssertionError as e:
        print(f"\n❌ ERRO: {e}\n")
        exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Não foi possível conectar ao servidor.")
        print("   Verifique se o servidor está rodando em http://localhost:8000\n")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}\n")
        exit(1)
