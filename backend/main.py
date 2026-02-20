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
import uuid
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta

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

# Armazenamento em memória do histórico de conversas por sessão
# Estrutura: {session_id: {"history": [...], "last_activity": datetime}}
sessions: Dict[str, Dict] = {}

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
        session_id: ID opcional da sessão (gerado automaticamente se não fornecido)
    """
    message: str
    session_id: Optional[str] = None

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
        history_size: Quantidade total de mensagens no histórico da sessão
        session_id: ID da sessão do usuário
    """
    response: str
    history_size: int
    session_id: str


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
    Cada usuário tem sua própria sessão isolada.

    Fluxo:
        1. Gera ou recupera session_id
        2. Adiciona mensagem do usuário ao histórico da sessão
        3. Aplica janela deslizante (últimas 6 mensagens)
        4. Envia contexto para API do Claude
        5. Armazena resposta do assistente
        6. Retorna resposta ao cliente

    Args:
        request: Objeto contendo a mensagem e session_id opcional

    Returns:
        ChatResponse com resposta do Claude, tamanho do histórico e session_id

    Raises:
        HTTPException (500): Erro ao processar mensagem ou comunicar com API
    """
    try:
        # Gerar ou usar session_id fornecido
        session_id = request.session_id or str(uuid.uuid4())

        # Inicializar sessão se não existir
        if session_id not in sessions:
            sessions[session_id] = {
                "history": [],
                "last_activity": datetime.now()
            }

        # Obter histórico da sessão
        session_data = sessions[session_id]
        conversation_history = session_data["history"]

        # Atualizar timestamp da última atividade
        session_data["last_activity"] = datetime.now()

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
            history_size=len(conversation_history),
            session_id=session_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar mensagem: {str(e)}")


class ClearRequest(BaseModel):
    """
    Modelo de dados para requisição de limpeza de histórico.

    Attributes:
        session_id: ID da sessão a ser limpa
    """
    session_id: str


@app.post("/clear")
async def clear_history(request: ClearRequest):
    """
    Limpa o histórico de conversas de uma sessão específica.

    Remove todas as mensagens armazenadas da sessão, reiniciando a conversa.
    Útil para começar uma nova sessão de chat.

    Args:
        request: Objeto contendo o session_id

    Returns:
        Dict com mensagem de confirmação

    Raises:
        HTTPException (404): Se a sessão não for encontrada
    """
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    sessions[request.session_id]["history"] = []
    sessions[request.session_id]["last_activity"] = datetime.now()

    return {"message": "Histórico limpo com sucesso", "session_id": request.session_id}


@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """
    Retorna histórico completo de conversas de uma sessão específica.

    Endpoint útil para debug e monitoramento do estado da conversa.
    Mostra todas as mensagens armazenadas, não apenas a janela deslizante.

    Args:
        session_id: ID da sessão a consultar

    Returns:
        Dict contendo:
            - session_id: ID da sessão consultada
            - total_messages: Número total de mensagens da sessão
            - window_size: Tamanho da janela deslizante configurada
            - history: Lista completa de mensagens (user + assistant)
            - last_activity: Timestamp da última atividade

    Raises:
        HTTPException (404): Se a sessão não for encontrada

    Note:
        Em produção, considere adicionar autenticação a este endpoint
        para proteger dados sensíveis da conversa.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    session_data = sessions[session_id]
    return {
        "session_id": session_id,
        "total_messages": len(session_data["history"]),
        "window_size": SLIDING_WINDOW_SIZE,
        "history": session_data["history"],
        "last_activity": session_data["last_activity"].isoformat()
    }


@app.get("/sessions")
async def list_sessions():
    """
    Lista todas as sessões ativas no servidor.

    Retorna informações resumidas sobre cada sessão ativa,
    incluindo número de mensagens e última atividade.

    Returns:
        Dict contendo:
            - total_sessions: Número total de sessões ativas
            - sessions: Lista de sessões com metadados

    Note:
        Este endpoint é útil para monitoramento e debug.
        Em produção, adicione autenticação adequada.
    """
    sessions_info = []
    for session_id, data in sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "total_messages": len(data["history"]),
            "last_activity": data["last_activity"].isoformat()
        })

    return {
        "total_sessions": len(sessions),
        "sessions": sessions_info
    }


@app.post("/cleanup-sessions")
async def cleanup_old_sessions(max_age_hours: int = 24):
    """
    Remove sessões inativas há mais de X horas.

    Libera memória removendo sessões que não têm atividade recente.
    Útil para manutenção automática do servidor.

    Args:
        max_age_hours: Idade máxima em horas (padrão: 24h)

    Returns:
        Dict com número de sessões removidas
    """
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    sessions_to_remove = [
        session_id for session_id, data in sessions.items()
        if data["last_activity"] < cutoff_time
    ]

    for session_id in sessions_to_remove:
        del sessions[session_id]

    return {
        "message": f"Limpeza concluída",
        "sessions_removed": len(sessions_to_remove),
        "sessions_remaining": len(sessions)
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
