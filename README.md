# Chat com Janela Deslizante - Claude AI

Projeto educacional de chat que usa a API da Anthropic (Claude) com implementação de **janela deslizante** para gerenciar contexto da conversa.

## 🤖 Modelo LLM Utilizado

Este projeto utiliza o **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`), o modelo mais rápido e econômico da família Claude 4.5, ideal para aplicações de chat que precisam de:
- Respostas rápidas e eficientes
- Menor custo por token (até 90% mais barato que Opus)
- Excelente qualidade para conversas gerais

## 📋 O que é Janela Deslizante?

A janela deslizante mantém apenas as **últimas 6 mensagens** (3 turnos de conversa) no contexto enviado para a API do Claude. Isso:
- Otimiza o uso de tokens
- Reduz custos de API drasticamente
- Mantém a conversa focada no contexto recente

## 🚀 Deploy no Railway (Plano Free)

### Pré-requisitos

1. **Conta na Anthropic**
   - Criar conta em: https://console.anthropic.com
   - Gerar API Key em: Settings > API Keys
   - Guardar a API Key (você precisará dela)

2. **Conta no Railway**
   - Criar conta gratuita em: https://railway.app
   - Plano free: $5/mês de crédito + 500 horas de execução

3. **Repositório Git**
   - Fazer fork ou push deste projeto para GitHub/GitLab

### Passo a Passo para Deploy

#### 1. Preparar o Repositório

```bash
# Certifique-se que todos os arquivos estão commitados
git add .
git commit -m "Preparar para deploy no Railway"
git push origin main
```

#### 2. Criar Projeto no Railway

1. Acesse https://railway.app e faça login
2. Clique em **"New Project"**
3. Selecione **"Deploy from GitHub repo"**
4. Escolha o repositório deste projeto
5. Railway vai detectar automaticamente que é um projeto Python

#### 3. Configurar Variáveis de Ambiente

1. No dashboard do projeto, clique em **"Variables"**
2. Adicione a variável:
   ```
   ANTHROPIC_API_KEY = sua_api_key_da_anthropic_aqui
   ```
3. Clique em **"Add"** para salvar

#### 4. Deploy Automático

- Railway vai automaticamente:
  - Detectar o `runtime.txt` e usar Python 3.11
  - Instalar dependências do `requirements.txt`
  - Executar o comando do `Procfile`
  - Iniciar o servidor na porta dinâmica

#### 5. Acessar a Aplicação

1. Aguarde o deploy finalizar (1-3 minutos)
2. Railway fornecerá uma URL pública:
   ```
   https://seu-projeto.up.railway.app
   ```
3. Abra a URL no navegador e teste o chat!

### 🔧 Solução de Problemas

#### Deploy falhou?
- Verifique os logs no Railway Dashboard
- Confirme que a `ANTHROPIC_API_KEY` está configurada
- Verifique se o `requirements.txt` tem todas as dependências

#### Erro 500 ao enviar mensagem?
- Verifique se a API Key está válida
- Confira os logs do servidor no Railway
- Teste a API Key localmente primeiro

#### Aplicação não abre?
- Aguarde alguns minutos após o deploy
- Verifique se o serviço está "Active" no Railway
- Confira se não excedeu o limite do plano free

### 💰 Limites do Plano Free

- **$5/mês** de crédito
- **500 horas/mês** de execução
- **100 GB/mês** de banda
- **1 GB RAM** por serviço

**Dica**: Para economizar créditos, pause o projeto quando não estiver usando:
- Railway Dashboard > Seu Projeto > Settings > Sleep on idle

## 🖥️ Executar Localmente

### 1. Clonar e Configurar

```bash
# Clonar repositório
git clone <url-do-repositorio>
cd TREINAMENTO_PROMPT_AVANCADO_JEDAI

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env e adicionar sua API Key
# ANTHROPIC_API_KEY=sua_api_key_aqui
```

### 3. Executar Servidor

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Acessar Aplicação

Abra o navegador em: http://localhost:8000

## 📁 Estrutura do Projeto

```
TREINAMENTO_PROMPT_AVANCADO_JEDAI/
├── backend/
│   └── main.py              # API FastAPI + lógica da janela deslizante
├── frontend/
│   ├── index.html           # Interface do chat
│   ├── style.css            # Estilos
│   └── script.js            # Lógica do frontend
├── tests/                   # Testes automatizados
├── .env.example             # Exemplo de variáveis de ambiente
├── .gitignore               # Arquivos ignorados pelo Git
├── Procfile                 # Comando de start para Railway
├── requirements.txt         # Dependências Python
├── runtime.txt              # Versão do Python
└── README.md               # Este arquivo
```

## 🧪 Executar Testes

```bash
# Rodar todos os testes
pytest

# Com cobertura
pytest --cov=backend --cov-report=html
```

## 🎯 Configurações da Janela Deslizante

Configurações no [backend/main.py](backend/main.py):

```python
MAX_MESSAGE_LENGTH = 2000        # Tamanho máximo por mensagem
SLIDING_WINDOW_SIZE = 6          # 6 mensagens = 3 turnos
```

Para alterar o tamanho da janela, modifique `SLIDING_WINDOW_SIZE`.

## 📚 API Endpoints

- `GET /` - Serve o frontend (index.html)
- `POST /chat` - Envia mensagem e recebe resposta do Claude
- `POST /clear` - Limpa histórico de conversas
- `GET /history` - Retorna histórico completo (debug)

## ⚠️ Notas de Segurança

Este projeto é **educacional** e usa configurações simplificadas:
- CORS permite qualquer origem (`allow_origins=["*"]`)
- Histórico em memória (perde dados ao reiniciar)
- Sem autenticação de usuários

**Para produção**, considere implementar:
- CORS restritivo
- Autenticação de usuários
- Persistência em banco de dados
- Rate limiting

## 📝 Licença

Projeto educacional para treinamento sobre janela deslizante e APIs de LLM.

## 🤝 Contribuindo

Este é um projeto de treinamento. Sinta-se livre para fazer fork e experimentar!

---

**Desenvolvido para treinamento Jedai - Prompts Avançados**
