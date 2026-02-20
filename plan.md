
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
    1. Definir: janela deslizante = últimas 6 mensagens 3 turnos
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

#### 🔴 Prioridade CRÍTICA (Segurança/Funcionalidade)
1. Implementar gerenciamento de sessões (substituir estado global compartilhado)
   - Criar session_id único por usuário
   - Armazenar históricos separados por sessão
   - Implementar limpeza automática de sessões antigas
2. Configurar CORS restritivo (substituir allow_origins=["*"])
   - Definir origens permitidas via variável de ambiente
   - Adicionar validação de referer
3. Implementar autenticação básica
   - Adicionar API key do cliente (diferente da Anthropic)
   - Validar requisições com header Authorization
4. Proteger endpoint /history
   - Adicionar autenticação obrigatória
   - Retornar apenas histórico da sessão do usuário
5. Implementar secret management
   - Usar variáveis de ambiente para todas credenciais
   - Adicionar validação de API key no startup

6. Refatorar arquitetura em camadas
   - Criar services/ (lógica de negócio)
   - Criar repositories/ (acesso a dados)
   - Criar models/ (schemas Pydantic)
   - Separar routers/ (endpoints)
7. Implementar persistência de dados
   - Adicionar Redis ou SQLite para histórico
   - Criar repository pattern para acesso aos dados
8. Externalizar configurações
   - Criar config.py com Settings do Pydantic
   - Mover model ID, limites e constantes para .env
9. Adicionar variáveis de ambiente para frontend
   - Criar config.js que lê de window.ENV
   - Configurar build process para diferentes ambientes
10. Implementar tratamento específico de erros
    - Criar exceções customizadas
    - Tratar erros específicos da API Anthropic
    - Retornar mensagens apropriadas ao usuário
11. Separar backend e frontend (arquitetura)
    - Remover StaticFiles do FastAPI
    - Documentar como servir frontend via nginx/CDN


12. Implementar sistema de logs
    - Adicionar logging estruturado (JSON)
    - Configurar níveis (DEBUG, INFO, WARNING, ERROR)
    - Log de requisições, erros e métricas
13. Adicionar rate limiting
    - Implementar limite por IP ou API key
    - Usar slowapi ou middleware customizado
14. Configurar ambientes (dev/staging/prod)
    - Criar .env.example, .env.dev, .env.prod
    - Documentar variáveis obrigatórias
15. Melhorar documentação OpenAPI
    - Adicionar descrições detalhadas
    - Criar exemplos de request/response
    - Documentar códigos de erro
16. Criar endpoints de observabilidade
    - Implementar /health (status do serviço)
    - Implementar /ready (dependências OK)
    - Implementar /metrics (Prometheus format)
17. Configurar timeout nas requisições
    - Adicionar timeout para API Anthropic
    - Implementar retry com backoff exponencial
18. Adicionar validações de segurança
    - Sanitizar input (prompt injection)
    - Validar tamanho total da requisição
    - Implementar content security policy


19. Configurar tipagem estrita
    - Adicionar mypy ao projeto
    - Configurar pyproject.toml com strict mode
    - Corrigir todos os erros de tipo
20. Implementar versionamento de API
    - Mover endpoints para /v1/
    - Preparar estrutura para v2
21. Adicionar compressão HTTP
    - Configurar GZipMiddleware
    - Testar compressão de respostas grandes
22. Renderizar markdown no frontend
    - Adicionar biblioteca (marked.js ou similar)
    - Sanitizar HTML com DOMPurify
    - Aplicar syntax highlighting para código
23. Implementar autenticação completa
    - Adicionar JWT tokens
    - Criar endpoint de login
    - Implementar refresh tokens
24. Criar suite completa de testes
    - Testes E2E com Playwright
    - Testes de carga com Locust
    - Testes de segurança (OWASP)
25. Configurar CI/CD
    - GitHub Actions para testes
    - Linting automático (ruff, black)
    - Deploy automatizado



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
    - [x] Definir: janela deslizante = últimas 6 mensagens 3 turnos
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

