import requests
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

response = requests.get('http://127.0.0.1:8000/history')
data = response.json()

print(f"\n{'='*60}")
print(f"HISTORICO DO CHAT - Total: {data['total_messages']} mensagens")
print(f"Janela deslizante: {data['window_size']} mensagens")
print(f"{'='*60}\n")

for i, msg in enumerate(data['history'], 1):
    role = "USUARIO" if msg['role'] == 'user' else "CLAUDE"
    print(f"[{i}] {role}:")
    print(f"    {msg['content']}\n")
