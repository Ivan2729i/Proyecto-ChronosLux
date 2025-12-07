
document.addEventListener("DOMContentLoaded", () => {
    const chatIcon = document.getElementById('chat-icon');
    const chatWindow = document.getElementById('chat-window');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input-text');
    const chatMessages = document.getElementById('chat-messages');

    if (chatIcon && chatWindow) {

        // Abrir
        chatIcon.addEventListener('click', () => {
            // Quitamos hidden para que se renderice, luego agregamos open para la animación
            chatWindow.classList.remove('hidden');
            // Pequeño timeout para permitir que el navegador procese el cambio de display antes de la opacidad
            setTimeout(() => {
                chatWindow.classList.add('open');
            }, 10);
        });

        // Cerrar
        const closeChat = () => {
            chatWindow.classList.remove('open');
            // Esperar a que termine la transición CSS (0.3s) antes de ocultar
            setTimeout(() => {
                if(!chatWindow.classList.contains('open')) {
                    chatWindow.classList.add('hidden');
                }
            }, 300);
        };

        if(closeChatBtn) closeChatBtn.addEventListener('click', closeChat);

        // Mensajería
        const addMessage = (text, className) => {
            const msg = document.createElement('div');
            msg.className = `message ${className}`;
            msg.textContent = text;
            chatMessages.appendChild(msg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            return msg;
        };

        const sendMessage = async () => {
            const text = chatInput.value.trim();
            if (!text) return;

            addMessage(text, 'user-message');
            chatInput.value = '';
            const botMsg = addMessage('...', 'bot-message');

            const csrftoken = window.getCookie('csrftoken');

            try {
                const response = await fetch('/api/chatbot/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                    body: JSON.stringify({ message: text })
                });

                if (!response.ok) throw new Error('Error');

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullText = '';

                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    fullText += decoder.decode(value, { stream: true });

                    // Renderizar Markdown si existe, si no texto plano
                    botMsg.innerHTML = (typeof marked !== 'undefined')
                        ? marked.parse(fullText)
                        : fullText;

                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            } catch (error) {
                botMsg.textContent = 'Error de conexión.';
            }
        };

        if(chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                sendMessage();
            });
        }
    }
});