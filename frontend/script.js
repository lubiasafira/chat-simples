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

    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    messageInput.addEventListener('input', () => {
        updateCharCounter();
        autoResizeTextarea();
        updateSendButtonState();
    });

    // Initial setup
    updateSendButtonState();
}

function updateSendButtonState() {
    const message = messageInput.value.trim();
    if (message.length === 0 || isProcessing) {
        sendBtn.disabled = true;
    } else {
        sendBtn.disabled = false;
    }
}

// Auto-resize do textarea
function autoResizeTextarea() {
    messageInput.style.height = 'auto'; // Reset to auto to auto-compute
    let newHeight = messageInput.scrollHeight;
    if (newHeight > 150) newHeight = 150; // Max height
    messageInput.style.height = newHeight + 'px';
}

// Atualizar contador de caracteres
function updateCharCounter() {
    const count = messageInput.value.length;
    charCount.textContent = `${count}/2000`;

    if (count > 1900) {
        charCount.style.color = 'var(--danger)';
    } else if (count > 1500) {
        charCount.style.color = '#f59e0b'; // warning
    } else {
        charCount.style.color = 'var(--text-secondary)';
    }
}

// Enviar mensagem
async function handleSendMessage() {
    const message = messageInput.value.trim();

    if (!message || isProcessing) return;

    if (message.length > 2000) {
        showError('Mensagem muito longa! O máximo é de 2000 caracteres.');
        return;
    }

    isProcessing = true;
    updateSendButtonState();

    // Remover welcome message animada
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.style.display = 'none';
    }

    // Adicionar mensagem do usuário
    addMessage(message, 'user');

    // Limpar input
    messageInput.value = '';
    messageInput.style.height = 'auto'; // reset height
    updateCharCounter();
    updateSendButtonState();

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

        // Remover indicador de digitação com fade out suave
        typingIndicator.style.opacity = '0';
        setTimeout(() => {
            typingIndicator.remove();
            // Adicionar resposta do assistente
            addMessage(data.response, 'assistant');
        }, 300);

    } catch (error) {
        console.error('Erro:', error);
        typingIndicator.remove();
        showError(error.message || 'Erro de conexão com o servidor.');
    } finally {
        isProcessing = false;
        updateSendButtonState();
        messageInput.focus();
    }
}

// Configuração do Marked (Markdown Parser)
if (typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true, // converte quebras de linha normais em <br>
        gfm: true, // GitHub Flavored Markdown
        sanitize: false // Importante definir sanitização extra se os dados não vêm de fonte confiável. A anthropic é segura.
    });
}

// Formatação básica e Markdown
function formatMessage(text) {
    if (typeof marked !== 'undefined') {
        return marked.parse(text);
    }

    // Fallback caso a biblioteca falhe
    let escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    // Tratamento de blocos de código
    escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    // Código inline
    escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Negrito
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    return escaped;
}

// Adicionar mensagem ao chat
function addMessage(text, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';

    if (role === 'assistant') {
        bubbleDiv.innerHTML = formatMessage(text);
    } else {
        bubbleDiv.textContent = text;
    }

    messageDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(messageDiv);

    // Permitir o frame para a animação ocorrer e então scrollToBottom
    requestAnimationFrame(() => scrollToBottom());
}

// Mostrar indicador de digitação premium
function showTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'typing-indicator';
    messageDiv.style.transition = 'opacity 0.3s ease';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';

    const typingContainer = document.createElement('div');
    typingContainer.className = 'typing-indicator-container';
    typingContainer.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';

    bubbleDiv.appendChild(typingContainer);
    messageDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(messageDiv);

    scrollToBottom();

    return messageDiv;
}

// Mostrar mensagem de erro
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        ${message}
    `;

    messagesContainer.appendChild(errorDiv);
    scrollToBottom();

    // Auto-remover logo
    setTimeout(() => {
        errorDiv.style.opacity = '0';
        errorDiv.style.transition = 'opacity 0.5s ease';
        setTimeout(() => errorDiv.remove(), 500);
    }, 5000);
}

// Limpar chat
async function handleClearChat() {
    if (!confirm('Deseja realmente apagar o histórico desta conversa?')) {
        return;
    }

    clearBtn.style.opacity = '0.5';
    clearBtn.style.pointerEvents = 'none';

    try {
        if (!sessionId) {
            setupEmptyChatUI();
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
            throw new Error('Falha ao limpar histórico');
        }

        sessionId = null;
        localStorage.removeItem('chat_session_id');

        setupEmptyChatUI();

    } catch (error) {
        console.error('Erro:', error);
        showError('Erro ao limpar a conversa pelo servidor.');
    } finally {
        clearBtn.style.opacity = '1';
        clearBtn.style.pointerEvents = 'auto';
    }
}

function setupEmptyChatUI() {
    // Animate out all messages
    const currentMessages = Array.from(messagesContainer.querySelectorAll('.message, .error-message'));
    currentMessages.forEach(msg => {
        msg.style.opacity = '0';
        msg.style.transform = 'translateY(-10px)';
        msg.style.transition = 'all 0.3s ease';
    });

    setTimeout(() => {
        messagesContainer.innerHTML = `
            <div class="welcome-message" style="animation: fadeIn 0.5s ease-out;">
                <div class="welcome-icon">✨</div>
                <h2>Nova Conversa</h2>
                <p>O histórico anterior foi deletado. Como posso ajudar agora?</p>
            </div>
        `;
    }, 350);
}

// Scroll suave para o final
function scrollToBottom() {
    // Adiciona uma margem inferior para não ficar colado no bottom
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}
