
## Perguntas
1. o que vai ser o projeto
    1. Um chat que usa janela deslizente
    2. Janela deslizente diz respeito a quantidade de chat que irão permanecer no contexto
    3. Vai pensir me memória apenas

2. Qual api? e como?
    1. Api claude api interface local usando python

3. Qual interface?
    1. Frontend HTML/CSS/JS com backend FastAPI

## Plano
Fase 0: Preparação
  - Criar conta Anthropic + gerar API key
  - Definir modelo (ex: claude-sonnet)
  - Testar chamada simples pelo terminal

### Fase 1: Setup Inicial
1. Estrutura de pastas
```
TREINAMENTO_PROMPT_AVANCADO_JEDAI/
├── backend/
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── .env
└── requirements.tx
```
2. Ambiente virtual Python
```bash
# Criar
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```
3. Dependências
fastapi
uvicorn
anthropic
python-dotenv

### Fase 2: Backend (FastAPI)
1. Configurar main.py básico (FastAPI + CORS)
    1. Definir: janela deslizante = últimas 20 mensagens 10 turnos
    2. Definir: tamanho máximo por mensagem = 2000 caracteres
2. Carregar variáveis de ambiente (.env)
3. Criar endpoint POST /chat
4. Implementar janela deslizante (histórico limitado a N mensagens)
5. Integrar com Claude API
6. Rodar servidor
```bash
uvicorn backend.main:app --reload
```

### Fase 3: Frontend (HTML/CSS/JS)
1. Criar index.html (estrutura, área de mensagens, input + botão)
2. Criar style.css (container, bolhas de mensagem, scroll)
3. Criar script.js (fetch, exibir mensagens, auto-scroll)

### Fase 4: Integração e Testes
1. Servir frontend via FastAPI (StaticFiles)
2. Testar fluxo completo (enviar mensagem, receber resposta)
3. Validar janela deslizante (histórico limitado)
4. Testar erros (API key inválida, servidor offline, mensagem vazia)
5. Ajustes finais (corrigir bugs, melhorar feedback)




## tarefas
### fase 0
- [x] Criar conta na Anthropic Console (https://console.anthropic.com)
- [x] Gerar API key no painel da Anthropic (Settings > API Keys)
- [x] Criar arquivo .env na raiz do projeto com ANTHROPIC_API_KEY
    - [x] criar um .gitignore
- [x] Criar script de teste (test_api.py) com chamada simples à API(claude-sonnet-4-5)
- [X] Executar teste via terminal para validar autenticação

### fase 1:
- [x] definir e aplicar estrutura do pasta
- [x] verificar injeção de dependêcencias

### fase 2:
- [x] Configurar main.py básico (FastAPI + CORS)
- [x] Carregar variáveis de ambiente (.env)
- [x] Criar endpoint POST /chat
- [x] Implementar janela deslizante (histórico limitado a N mensagens)
    - [x] Definir: janela deslizante = últimas 20 mensagens 10 turnos
    - [x] Definir: tamanho máximo por mensagem = 2000 caracteres
- [x] Integrar com Claude API
- [x] Rodar servidor
```bash
uvicorn backend.main:app --reload
```
- [x] Criar teste para garantir a resposta e comportamento da api

### Fase 3: Frontend (HTML/CSS/JS)
- [x] Criar index.html (estrutura, área de mensagens, input + botão)
- [x] Criar style.css (container, bolhas de mensagem, scroll)
- [x] Criar script.js (fetch, exibir mensagens, auto-scroll)

### Fase 4: Integração e Testes
- [x] Servir frontend via FastAPI (StaticFiles)
- [x] Testar fluxo completo (enviar mensagem, receber resposta)
- [x] Validar janela deslizante (histórico limitado)
- [x] Testar erros (API key inválida, servidor offline, mensagem vazia)
- [x] Ajustes finais (corrigir bugs, melhorar feedback)

### Fase 5: Melhorias e Refatorações
- [ ] refatorar em módulos backend/main.py
    - [x] corrigir Estado global compartilhado entre todos os usuários
    - [ ] CORS totalmente aberto
- [x] Troca o modulo LLM para Haiku
- [x] Criar sessões para cada usuário
- [ ] limitar requisão a api
- [x] aumentar a quandidade da janela deslizante para 10 turnos

## Fase 6: melhorias no frontend
- [ ] implemente nova frontend utilizando gemini 3.1



