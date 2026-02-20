"""
Backend FastAPI para chat com Claude AI usando janela deslizante.

Este módulo implementa uma API REST que permite conversar com Claude
mantendo apenas as últimas 6 mensagens no contexto (janela deslizante).
Isso otimiza o uso de tokens e mantém a conversa focada.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from anthropic import Anthropic
from dotenv import load_dotenv
import os
from typing import List, Dict
from pathlib import Path

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MAX_MESSAGE_LENGTH = 2000
SLIDING_WINDOW_SIZE = 6  # 6 mensagens = 3 turnos (user + assistant)

# Inicializar FastAPI
app = FastAPI(title="Chat com Janela Deslizante")

# Configurar CORS
# NOTA: allow_origins=["*"] permite qualquer origem - usado apenas para fins educacionais
# Em produção, especifique os domínios permitidos: ["https://seudominio.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar cliente Anthropic
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY não encontrada no arquivo .env")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Armazenamento em memória do histórico de conversas
conversation_history: List[Dict[str, str]] = []

# Configurar servir arquivos estáticos (frontend)
# Obter caminho absoluto do diretório frontend
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Montar o diretório de arquivos estáticos
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


class ChatRequest(BaseModel):
    """
    Modelo de dados para requisição de chat.

    Attributes:
        message: Texto da mensagem do usuário (máx 2000 caracteres)
    """
    message: str

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """
        Valida e normaliza mensagem do usuário.

        Args:
            v: Mensagem a ser validada

        Returns:
            Mensagem normalizada (sem espaços nas pontas)

        Raises:
            ValueError: Se mensagem vazia ou excede limite de caracteres
        """
        if not v or not v.strip():
            raise ValueError("Mensagem não pode estar vazia")
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"Mensagem excede o limite de {MAX_MESSAGE_LENGTH} caracteres")
        return v.strip()


class ChatResponse(BaseModel):
    """
    Modelo de dados para resposta de chat.

    Attributes:
        response: Texto da resposta gerada pelo Claude
        history_size: Quantidade total de mensagens no histórico
    """
    response: str
    history_size: int


@app.get("/")
async def root():
    """
    Endpoint raiz da API que serve o frontend.

    Retorna o arquivo index.html do frontend para iniciar a aplicação de chat.

    Returns:
        FileResponse: Arquivo HTML do frontend
    """
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend não encontrado")
    return FileResponse(index_path)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Processa mensagem do usuário e retorna resposta do Claude.

    Implementa janela deslizante: mantém apenas as últimas 6 mensagens
    (3 turnos de conversa) no contexto enviado para a API do Claude.

    Fluxo:
        1. Adiciona mensagem do usuário ao histórico
        2. Aplica janela deslizante (últimas 6 mensagens)
        3. Envia contexto para API do Claude
        4. Armazena resposta do assistente
        5. Retorna resposta ao cliente

    Args:
        request: Objeto contendo a mensagem do usuário

    Returns:
        ChatResponse com resposta do Claude e tamanho do histórico

    Raises:
        HTTPException (500): Erro ao processar mensagem ou comunicar com API
    """
    try:
        # Adicionar mensagem do usuário ao histórico
        conversation_history.append({
            "role": "user",
            "content": request.message
        })

        # Aplicar janela deslizante (manter apenas as últimas N mensagens)
        sliding_window = conversation_history[-SLIDING_WINDOW_SIZE:] if len(conversation_history) > SLIDING_WINDOW_SIZE else conversation_history

        # Chamar Claude API
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=sliding_window
        )

        # Extrair resposta do assistant
        assistant_message = response.content[0].text

        # Adicionar resposta do assistant ao histórico
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Retornar resposta
        return ChatResponse(
            response=assistant_message,
            history_size=len(conversation_history)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar mensagem: {str(e)}")


@app.post("/clear")
async def clear_history():
    """
    Limpa todo o histórico de conversas da memória.

    Remove todas as mensagens armazenadas, reiniciando a conversa.
    Útil para começar uma nova sessão de chat.

    Returns:
        Dict com mensagem de confirmação
    """
    global conversation_history
    conversation_history = []
    return {"message": "Histórico limpo com sucesso"}


@app.get("/history")
async def get_history():
    """
    Retorna histórico completo de conversas.

    Endpoint útil para debug e monitoramento do estado da conversa.
    Mostra todas as mensagens armazenadas, não apenas a janela deslizante.

    Returns:
        Dict contendo:
            - total_messages: Número total de mensagens
            - window_size: Tamanho da janela deslizante configurada
            - history: Lista completa de mensagens (user + assistant)

    Note:
        Em produção, considere adicionar autenticação a este endpoint
        para proteger dados sensíveis da conversa.
    """
    return {
        "total_messages": len(conversation_history),
        "window_size": SLIDING_WINDOW_SIZE,
        "history": conversation_history
    }


@app.get("/health")
async def health_check():
    """
    Verifica se a API está funcionando e se a API Key está configurada.

    Returns:
        Dict com status da aplicação e configuração da API Key
    """
    api_key_configured = bool(ANTHROPIC_API_KEY)
    api_key_preview = f"{ANTHROPIC_API_KEY[:8]}..." if api_key_configured and len(ANTHROPIC_API_KEY) > 8 else "Not configured"

    # Testar conexão com a API da Anthropic
    api_working = False
    error_message = None
    try:
        test_response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        api_working = True
    except Exception as e:
        error_message = str(e)

    return {
        "status": "healthy" if api_working else "unhealthy",
        "api_key_configured": api_key_configured,
        "api_key_preview": api_key_preview,
        "anthropic_api_working": api_working,
        "error": error_message
    }
