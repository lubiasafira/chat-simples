// Configuração da API
// Detecta automaticamente se está em produção ou desenvolvimento local
const API_URL = window.location.origin.includes('railway.app')
    ? window.location.origin
    : 'http://localhost:8000';

// Elementos do DOM
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-btn');
const charCount = document.getElementById('char-count');

// Estado
let isProcessing = false;
let sessionId = localStorage.getItem('chat_session_id') || null;

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    messageInput.focus();
});

// Event Listeners
function setupEventListeners() {
    sendBtn.addEventListener('click', handleSendMessage);
    clearBtn.addEventListener('click', handleClearChat);

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    messageInput.addEventListener('input', () => {
        updateCharCounter();
        autoResizeTextarea();
    });
}

// Auto-resize do textarea
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = messageInput.scrollHeight + 'px';
}

// Atualizar contador de caracteres
function updateCharCounter() {
    const count = messageInput.value.length;
    charCount.textContent = count;

    if (count > 1800) {
        charCount.style.color = '#ff4444';
    } else if (count > 1500) {
        charCount.style.color = '#ff9800';
    } else {
        charCount.style.color = '#6c757d';
    }
}

// Enviar mensagem
async function handleSendMessage() {
    const message = messageInput.value.trim();

    if (!message || isProcessing) return;

    if (message.length > 2000) {
        showError('Mensagem muito longa! Máximo de 2000 caracteres.');
        return;
    }

    isProcessing = true;
    sendBtn.disabled = true;

    // Adicionar mensagem do usuário
    addMessage(message, 'user');

    // Limpar input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    updateCharCounter();

    // Mostrar indicador de digitação
    const typingIndicator = showTypingIndicator();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                session_id: sessionId
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao enviar mensagem');
        }

        const data = await response.json();

        // Armazenar session_id recebido do servidor
        if (data.session_id && data.session_id !== sessionId) {
            sessionId = data.session_id;
            localStorage.setItem('chat_session_id', sessionId);
        }

        // Remover indicador de digitação
        typingIndicator.remove();

        // Adicionar resposta do assistente
        addMessage(data.response, 'assistant');

    } catch (error) {
        console.error('Erro:', error);
        typingIndicator.remove();
        showError(error.message || 'Erro ao se comunicar com o servidor. Verifique se o backend está rodando.');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

// Adicionar mensagem ao chat
function addMessage(text, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.textContent = text;

    messageDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(messageDiv);

    scrollToBottom();
}

// Mostrar indicador de digitação
function showTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'typing-indicator';

    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';

    messageDiv.appendChild(typingDiv);
    messagesContainer.appendChild(messageDiv);

    scrollToBottom();

    return messageDiv;
}

// Mostrar mensagem de erro
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = '⚠️ ' + message;

    messagesContainer.appendChild(errorDiv);
    scrollToBottom();

    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Limpar chat
async function handleClearChat() {
    if (!confirm('Tem certeza que deseja limpar toda a conversa?')) {
        return;
    }

    try {
        // Se não houver session_id, apenas limpar a interface
        if (!sessionId) {
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <p>👋 Olá! Sou o Claude. Como posso ajudar você hoje?</p>
                </div>
            `;
            return;
        }

        const response = await fetch(`${API_URL}/clear`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: sessionId }),
        });

        if (!response.ok) {
            throw new Error('Erro ao limpar histórico');
        }

        // Gerar novo session_id para começar uma nova conversa
        sessionId = null;
        localStorage.removeItem('chat_session_id');

        // Limpar interface
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <p>👋 Olá! Sou o Claude. Como posso ajudar você hoje?</p>
            </div>
        `;

    } catch (error) {
        console.error('Erro:', error);
        showError('Erro ao limpar conversa');
    }
}

// Scroll automático para o final
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
