document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide icons
    const lucide = window.lucide;
    if (lucide) {
        lucide.createIcons();
    }

    // Tailwind configuration
    tailwind.config = {
        theme: {
            extend: {
                colors: {
                    primary: '#090C27',
                    'primary-foreground': '#ffffff',
                    secondary: '#d4af37',
                    'secondary-foreground': '#090C27',
                    background: '#ffffff',
                    foreground: '#1f2937',
                    muted: '#f3f4f6',
                    'muted-foreground': '#6b7280',
                    border: '#e5e7eb'
                },
                fontFamily: {
                    'serif': ['Montserrat', 'serif'],
                    'sans': ['Open Sans', 'sans-serif']
                }
            }
        }
    }

    // --- LÓGICA DEL MENÚ MÓVIL ---
    document.getElementById('mobile-menu-btn').addEventListener('click', function() {
        const menu = document.getElementById('mobile-menu');
        const icon = this.querySelector('i');

        menu.classList.toggle('hidden');

        if (menu.classList.contains('hidden')) {
            icon.setAttribute('data-lucide', 'menu');
        } else {
            icon.setAttribute('data-lucide', 'x');
        }
        lucide.createIcons();
    });


    // --- INICIO: BLOQUE DE CÓDIGO COMPLETO PARA EL CARRITO ---

    // Función para obtener el token CSRF de Django
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Función para actualizar el ícono del contador en el navbar
    function updateCartIcon(total_items) {
        const cartCount = document.getElementById('cart-count');
        if (!cartCount) return;
        if (total_items > 0) {
            cartCount.textContent = total_items;
            cartCount.classList.remove('hidden');
        } else {
            cartCount.textContent = '0';
            cartCount.classList.add('hidden');
        }
    }

    // Función para pedir los datos del carrito a Django y dibujar el modal
    async function renderCartModal() {
        try {
            const response = await fetch('/api/carrito/');
            const data = await response.json();

            const cartItemsContainer = document.getElementById('cart-items');
            const cartTotalEl = document.getElementById('cart-total');
            const checkoutBtn = document.getElementById('checkout-btn');
            if (!cartItemsContainer || !cartTotalEl || !checkoutBtn) return;

            cartItemsContainer.innerHTML = '';

            if (data.cart_items.length === 0) {
                cartItemsContainer.innerHTML = '<p class="text-gray-500 text-center">Tu carrito está vacío</p>';
                checkoutBtn.classList.add('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
                checkoutBtn.setAttribute('aria-disabled', 'true');
            } else {
                data.cart_items.forEach(item => {
                    const itemHTML = `
                        <div class="flex items-center space-x-4 mb-4 p-4 border rounded-lg">
                            <img src="/media/${item.image_url}" alt="${item.name}" class="w-16 h-16 object-cover rounded">
                            <div class="flex-1">
                                <h3 class="font-semibold">${item.brand} ${item.name}</h3>
                                <p class="text-gray-600">$${item.price.toFixed(2)}</p>
                                <div class="flex items-center space-x-2 mt-2">
                                    <button class="quantity-btn border px-2 rounded" data-id="${item.id}" data-action="decrease">-</button>
                                    <span>${item.quantity}</span>
                                    <button class="quantity-btn border px-2 rounded" data-id="${item.id}" data-action="increase">+</button>
                                    <button class="remove-btn ml-auto text-red-500 hover:text-red-700 font-semibold" data-id="${item.id}">Eliminar</button>
                                </div>
                            </div>
                        </div>
                    `;
                    cartItemsContainer.innerHTML += itemHTML;
                });
                checkoutBtn.classList.remove('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
                checkoutBtn.setAttribute('aria-disabled', 'false');
            }
            cartTotalEl.textContent = `$${data.total_price.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            updateCartIcon(data.total_items);
        } catch (error) {
            console.error("Error al renderizar el carrito:", error);
        }
    }

    // Event listener unificado para todas las acciones
    document.body.addEventListener('click', async function(event) {
        const button = event.target.closest('button');

        // Abrir/cerrar modal del carrito
        if (event.target.closest('#cart-btn')) {
            document.getElementById('cart-modal')?.classList.remove('hidden');
            renderCartModal();
        }
        if (event.target.closest('#close-cart')) {
            document.getElementById('cart-modal')?.classList.add('hidden');
        }

        // Si no fue un botón, no hacemos más
        if (!button) return;

        let url;
        let watchId;

        // Acciones del carrito
        if (button.matches('.add-to-cart')) {
            event.preventDefault();
            watchId = button.dataset.watchId;
            url = `/carrito/agregar/${watchId}/`;
            const response = await fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrftoken } });
            const data = await response.json();
            if (data.status === 'ok') updateCartIcon(data.total_items);
        }
        if (button.matches('.remove-btn')) {
            watchId = button.dataset.id;
            url = `/carrito/eliminar/${watchId}/`;
            const response = await fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrftoken } });
            if ((await response.json()).status === 'ok') renderCartModal();
        }
        if (button.matches('.quantity-btn')) {
            watchId = button.dataset.id;
            const action = button.dataset.action;
            url = `/carrito/actualizar/${watchId}/`;
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: action })
            });
            if ((await response.json()).status === 'ok') renderCartModal();
        }
    });

    // --- FIN: BLOQUE DE CÓDIGO COMPLETO PARA EL CARRITO ---


    // --- LÓGICA DEL MODAL DE USUARIO ---

    const userIconBtn = document.getElementById('user-icon-btn');
    const userModal = document.getElementById('user-modal');
    const closeModal = document.getElementById('close-modal');
    const _switchToRegister = document.getElementById('switch-to-register');
    const switchToRegisterBtn = _switchToRegister ? _switchToRegister.querySelector('a') : null;
    const _switchToLogin = document.getElementById('switch-to-login');
    const switchToLoginBtn = _switchToLogin ? _switchToLogin.querySelector('a') : null;
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const modalTitle = document.getElementById('modal-title');
    const switchTextLogin = document.getElementById('switch-to-login');
    const switchTextRegister = document.getElementById('switch-to-register');

    if (userIconBtn) {
        userIconBtn.addEventListener('click', () => {
            if (userModal) { userModal.classList.remove('hidden'); }
        });
    }

    if (closeModal) {
        closeModal.addEventListener('click', () => {
            if (userModal) { userModal.classList.add('hidden'); }
        });
    }

    if (switchToRegisterBtn) {
        switchToRegisterBtn.addEventListener('click', (e) => {
            e.preventDefault();
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            modalTitle.textContent = 'Regístrate';
            switchTextRegister.classList.add('hidden');
            switchTextLogin.classList.remove('hidden');
        });
    }

    if (switchToLoginBtn) {
        switchToLoginBtn.addEventListener('click', (e) => {
            e.preventDefault();
            registerForm.classList.add('hidden');
            loginForm.classList.remove('hidden');
            modalTitle.textContent = 'Iniciar sesión';
            switchTextLogin.classList.add('hidden');
            switchTextRegister.classList.remove('hidden');
        });
    }

    // --- FIN LÓGICA DEL MODAL DE USUARIO ---

    //  --- INICIO: CÓDIGO DE RESEÑAS ---

    const starRatingContainer = document.getElementById('star-rating');
    if (starRatingContainer) {
        const ratingInput = document.getElementById('id_calificacion');

        const paintStars = (rating) => {
            const stars = starRatingContainer.querySelectorAll('[data-lucide="star"]');

            stars.forEach(star => {
                const starValue = parseInt(star.dataset.value, 10);
                if (starValue <= rating) {
                    star.classList.add('fill-yellow-400', 'text-yellow-400');
                    star.classList.remove('text-gray-300');
                } else {
                    star.classList.remove('fill-yellow-400', 'text-yellow-400');
                    star.classList.add('text-gray-300');
                }
            });
        };

        // Evento de clic en una estrella
        starRatingContainer.addEventListener('click', function(e) {
            const star = e.target.closest('[data-lucide="star"]');
            if (star) {
                const ratingValue = star.dataset.value;
                if (ratingInput) ratingInput.value = ratingValue;
                paintStars(ratingValue);
            }
        });

        // Evento para restaurar las estrellas al último valor guardado
        starRatingContainer.addEventListener('mouseout', function() {
            if (ratingInput) paintStars(ratingInput.value || 0);
        });

        // Evento para pre-iluminar al pasar el mouse
        starRatingContainer.addEventListener('mouseover', function(e) {
            const star = e.target.closest('[data-lucide="star"]');
            if (star) {
                paintStars(star.dataset.value);
            }
        });

        // Pintar el estado inicial al cargar la página
        if (ratingInput) {
            paintStars(ratingInput.value || 0);
        }
    }

    // --- FIN: CÓDIGO DE RESEÑAS ---

    // --- INICIO: CÓDIGO DEL CHATBOT ---
    const chatIcon = document.getElementById('chat-icon');
    const chatWindow = document.getElementById('chat-window');
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input-text');
    const closeChatBtn = document.getElementById('close-chat-btn');

    // Abrir y cerrar la ventana de chat
    chatIcon?.addEventListener('click', () => {
        chatWindow?.classList.toggle('open');
        chatWindow?.classList.toggle('hidden');
    });
    closeChatBtn?.addEventListener('click', () => {
        chatWindow?.classList.remove('open');
        chatWindow?.classList.add('hidden');
    });

    // Función para añadir un mensaje al contenedor
    const addMessage = (text, className) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    };

    // Función para enviar el mensaje
    const sendMessage = async () => {
        const message = chatInput.value.trim();
        if (message === '') return;

        addMessage(message, 'user-message');
        chatInput.value = '';
        const botMessageContainer = addMessage('Escribiendo...', 'bot-message');

        try {
            const response = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                botMessageContainer.textContent = 'Lo siento, hubo un error.';
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let botResponseMarkdown = '';

            while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            botResponseMarkdown += chunk;

            botMessageContainer.innerHTML = marked.parse(botResponseMarkdown);

            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

    } catch (error) {
            botMessageContainer.textContent = 'Lo siento, no pude obtener una respuesta.';
            console.error('Error en el fetch del chatbot:', error);
        }
    };

    // Event Listeners para enviar el mensaje
    chatForm?.addEventListener('submit', (e) => {
        e.preventDefault();
        sendMessage();
    });

//  --- FIN: CÓDIGO DEL CHATBOT ---
});

// Fallback robusto para abrir/cerrar el modal por delegación
document.addEventListener('click', (e) => {
  if (e.target.closest('#user-icon-btn')) {
    const modal = document.getElementById('user-modal');
    if (modal) modal.classList.remove('hidden');
  }
  if (e.target.closest('#close-modal')) {
    const modal = document.getElementById('user-modal');
    if (modal) modal.classList.add('hidden');
  }
});
