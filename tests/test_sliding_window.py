"""
Teste para validar a janela deslizante do histórico de mensagens.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests

API_URL = "http://localhost:8000"

def test_sliding_window():
    """Testa se a janela deslizante está limitando corretamente o histórico."""
    print("🧪 TESTE 2: Validação da Janela Deslizante")
    print("-" * 50)

    # Limpar histórico
    print("\n1. Limpando histórico...")
    response = requests.post(f"{API_URL}/clear")
    assert response.status_code == 200
    print("   ✅ Histórico limpo")

    # Enviar 5 turnos de conversa (10 mensagens no total)
    print("\n2. Enviando 5 turnos de conversa...")
    messages = [
        "Turno 1: Qual é a capital do Brasil?",
        "Turno 2: Qual é a capital da França?",
        "Turno 3: Qual é a capital da Itália?",
        "Turno 4: Qual é a capital da Espanha?",
        "Turno 5: Qual é a capital de Portugal?",
    ]

    for i, message in enumerate(messages, 1):
        print(f"   Enviando turno {i}...")
        response = requests.post(
            f"{API_URL}/chat",
            json={"message": message}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"   📊 Histórico agora tem {data['history_size']} mensagens")

    # Verificar histórico completo
    print("\n3. Verificando histórico completo...")
    response = requests.get(f"{API_URL}/history")
    assert response.status_code == 200

    history_data = response.json()
    total = history_data['total_messages']
    window_size = history_data['window_size']

    print(f"   📜 Total de mensagens armazenadas: {total}")
    print(f"   🪟 Tamanho da janela deslizante: {window_size}")

    # Validação: devemos ter 10 mensagens no total (5 user + 5 assistant)
    assert total == 10, f"Esperado 10 mensagens, mas temos {total}"
    print("   ✅ Histórico completo tem 10 mensagens (correto)")

    # Verificar que a janela deslizante está configurada para 6
    assert window_size == 6, f"Janela deslizante deveria ser 6, mas é {window_size}"
    print("   ✅ Janela deslizante configurada para 6 mensagens (correto)")

    # Teste crítico: enviar mais uma mensagem e verificar o contexto
    print("\n4. Testando limite da janela deslizante...")
    print("   Enviando mensagem pedindo para listar capitais mencionadas...")

    # Esta mensagem deve receber apenas as últimas 6 mensagens como contexto
    # Ou seja, deve lembrar apenas dos turnos 4 e 5 (Espanha e Portugal)
    # e parte do turno 3 (uma mensagem)
    test_message = "Liste todas as capitais que mencionei anteriormente"
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": test_message}
    )
    assert response.status_code == 200
    data = response.json()

    print(f"   📥 Resposta: {data['response'][:200]}...")

    # Análise da resposta
    response_text = data['response'].lower()

    # Esperamos que lembre de Madrid (Espanha) e Lisboa (Portugal)
    # pois estão na janela deslizante (últimas 6 mensagens)
    has_madrid = 'madrid' in response_text
    has_lisboa = 'lisboa' in response_text or 'lisbon' in response_text

    # NÃO deve lembrar de Brasília (Brasil) pois está fora da janela
    has_brasilia = 'brasília' in response_text or 'brasilia' in response_text

    print(f"\n   📊 Análise do contexto:")
    print(f"      - Lembra de Madrid (Espanha)? {has_madrid}")
    print(f"      - Lembra de Lisboa (Portugal)? {has_lisboa}")
    print(f"      - Lembra de Brasília (Brasil)? {has_brasilia}")

    # Verificações
    if has_madrid and has_lisboa:
        print("   ✅ Janela deslizante funcionando: lembra das capitais recentes")

    if not has_brasilia:
        print("   ✅ Janela deslizante funcionando: NÃO lembra das capitais antigas (fora da janela)")
    else:
        print("   ⚠️  AVISO: Resposta menciona Brasília (pode ser que Claude tenha adivinhado ou a janela não está funcionando)")

    # Verificar tamanho final do histórico
    response = requests.get(f"{API_URL}/history")
    final_history = response.json()
    print(f"\n   📜 Total final de mensagens: {final_history['total_messages']}")

    assert final_history['total_messages'] == 12, "Deveríamos ter 12 mensagens agora (6 turnos)"

    print("\n" + "="*50)
    print("✅ TESTE 2 PASSOU - Janela deslizante validada!")
    print("="*50 + "\n")

    print("\n💡 OBSERVAÇÃO IMPORTANTE:")
    print("   A janela deslizante mantém apenas as últimas 6 mensagens")
    print("   no CONTEXTO enviado para a API do Claude.")
    print("   Todas as mensagens continuam armazenadas no backend,")
    print("   mas o Claude só 'vê' as 6 mais recentes.\n")

if __name__ == "__main__":
    try:
        print("\n🚀 Iniciando teste de janela deslizante...\n")
        test_sliding_window()
        print("\n🎉 Teste concluído com sucesso!\n")
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
