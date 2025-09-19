document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide icons (solo una vez)
    const lucide = window.lucide;
    if (lucide) {
        lucide.createIcons();
    }

    // Tailwind configuration (se queda igual)
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

    // --- LÓGICA DEL MENÚ MÓVIL (SE QUEDA IGUAL) ---
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


    // --- INICIO DE LA NUEVA LÓGICA DEL CARRITO (JS + DJANGO) ---

    // Función para obtener el token CSRF (esencial para la seguridad de Django)
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

    // Funcionalidad del MODAL del carrito
    document.getElementById('cart-btn').addEventListener('click', function() {
        document.getElementById('cart-modal').classList.remove('hidden');
        renderCartModal(); // Al abrir el modal, lo renderizamos con datos frescos del servidor.
    });

    document.getElementById('close-cart').addEventListener('click', function() {
        document.getElementById('cart-modal').classList.add('hidden');
    });

    /**
     * Pide los datos del carrito a Django y actualiza el HTML del modal.
     */
    async function renderCartModal() {
        const response = await fetch('/api/carrito/');
        const data = await response.json();

        const cartItemsContainer = document.getElementById('cart-items');
        const cartTotalEl = document.getElementById('cart-total');
        const checkoutBtn = document.getElementById('checkout-btn');

        cartItemsContainer.innerHTML = ''; // Limpiamos el contenido anterior

        if (data.cart_items.length === 0) {
            cartItemsContainer.innerHTML = '<p class="text-gray-500 text-center">Tu carrito está vacío</p>';
            checkoutBtn.disabled = true;
            checkoutBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            data.cart_items.forEach(item => {
                const itemHTML = `
                    <div class="flex items-center space-x-4 mb-4 p-4 border rounded-lg">
                        <img src="/static/img/${item.image_url}" alt="${item.name}" class="w-16 h-16 object-cover rounded">
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
            checkoutBtn.disabled = false;
            checkoutBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }

        cartTotalEl.textContent = `$${data.total_price.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        updateCartIcon(data.total_items);
    }

    /**
     * Escuchador de eventos principal para todas las acciones del carrito
     */
    document.body.addEventListener('click', async function(event) {
        const button = event.target.closest('button');
        if (!button) return;

        let url;
        let watchId;
        const headers = { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/json' };

        // --- AGREGAR AL CARRITO ---
        if (button.matches('.add-to-cart')) {
            event.preventDefault();
            watchId = button.dataset.watchId;
            url = `/carrito/agregar/${watchId}/`;

            const response = await fetch(url, { method: 'POST', headers: headers });
            const data = await response.json();

            if (data.status === 'ok') {
                updateCartIcon(data.total_items);
            }
        }

        // --- ELIMINAR DEL CARRITO ---
        if (button.matches('.remove-btn')) {
            watchId = button.dataset.id;
            url = `/carrito/eliminar/${watchId}/`;

            const response = await fetch(url, { method: 'POST', headers: headers });
            const data = await response.json();

            if (data.status === 'ok') {
                renderCartModal(); // Re-renderiza el modal con los datos actualizados
            }
        }

        // --- ACTUALIZAR CANTIDAD ---
        if (button.matches('.quantity-btn')) {
            watchId = button.dataset.id;
            const action = button.dataset.action;
            url = `/carrito/actualizar/${watchId}/`;

            const response = await fetch(url, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ action: action })
            });
            const data = await response.json();

            if (data.status === 'ok') {
                renderCartModal(); // Re-renderiza el modal
            }
        }
    });


     // Función auxiliar para actualizar solo el ícono del contador en el navbar.

    function updateCartIcon(total_items) {
        const cartCount = document.getElementById('cart-count');
        if (cartCount) {
             if (total_items > 0) {
                cartCount.textContent = total_items;
                cartCount.classList.remove('hidden');
            } else {
                cartCount.classList.add('hidden');
            }
        }
    }



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