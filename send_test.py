import requests
import json
import sys

# Configurar encoding UTF-8 no Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"message": "Ola! Qual e a capital do Brasil?"}
    )

    if response.status_code == 200:
        data = response.json()
        print("\n[OK] MENSAGEM ENVIADA COM SUCESSO!\n")
        print(f"Resposta do Claude:\n{data['response']}\n")
        print(f"Historico tem {data['history_size']} mensagens")
    else:
        print(f"[ERRO] Status: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"[ERRO] Ao conectar: {e}")
    print("\nCertifique-se que o servidor esta rodando!")
