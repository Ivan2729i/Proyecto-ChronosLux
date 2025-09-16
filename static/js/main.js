document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide icons (solo una vez)
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

    // Cart functionality
    let cart = [];

    // Mobile menu toggle
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

    // Cart modal functionality
    document.getElementById('cart-btn').addEventListener('click', function() {
        document.getElementById('cart-modal').classList.remove('hidden');
    });

    document.getElementById('close-cart').addEventListener('click', function() {
        document.getElementById('cart-modal').classList.add('hidden');
    });

    // Add to cart functionality (This part seems to be from another file, but we'll keep it)
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const watchData = {
                id: parseInt(this.dataset.watchId),
                name: this.dataset.watchName,
                brand: this.dataset.watchBrand,
                price: parseFloat(this.dataset.watchPrice),
                image: this.dataset.watchImage,
                quantity: 1
            };

            addToCart(watchData);
        });
    });

    function addToCart(watch) {
        const existingItem = cart.find(item => item.id === watch.id);

        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cart.push(watch);
        }

        updateCartUI();
    }

    function updateCartUI() {
        const cartCount = document.getElementById('cart-count');
        const cartItems = document.getElementById('cart-items');
        const cartTotal = document.getElementById('cart-total');
        const checkoutBtn = document.getElementById('checkout-btn');

        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        const totalPrice = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

        // Update cart count
        if (totalItems > 0) {
            cartCount.textContent = totalItems;
            cartCount.classList.remove('hidden');
        } else {
            cartCount.classList.add('hidden');
        }

        // Update cart items
        if (cart.length === 0) {
            cartItems.innerHTML = '<p class="text-gray-500 text-center">Tu carrito está vacío</p>';
            checkoutBtn.disabled = true;
        } else {
            cartItems.innerHTML = cart.map(item => `
                <div class="flex items-center space-x-4 mb-4 p-4 border rounded-lg">
                    <img src="${item.image}" alt="${item.name}" class="w-16 h-16 object-cover rounded">
                    <div class="flex-1">
                        <h3 class="font-semibold">${item.brand} ${item.name}</h3>
                        <p class="text-gray-600">$${item.price}</p>
                        <div class="flex items-center space-x-2 mt-2">
                            <button class="quantity-btn" data-id="${item.id}" data-action="decrease">-</button>
                            <span>${item.quantity}</span>
                            <button class="quantity-btn" data-id="${item.id}" data-action="increase">+</button>
                            <button class="remove-btn ml-4 text-red-500" data-id="${item.id}">Eliminar</button>
                        </div>
                    </div>
                </div>
            `).join('');
            checkoutBtn.disabled = false;
        }

        // Update total
        cartTotal.textContent = `$${totalPrice.toLocaleString()}`;

        // Add event listeners for quantity and remove buttons
        document.querySelectorAll('.quantity-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = parseInt(this.dataset.id);
                const action = this.dataset.action;
                updateQuantity(id, action);
            });
        });

        document.querySelectorAll('.remove-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = parseInt(this.dataset.id);
                removeFromCart(id);
            });
        });
    }

    function updateQuantity(id, action) {
        const item = cart.find(item => item.id === id);
        if (item) {
            if (action === 'increase') {
                item.quantity += 1;
            } else if (action === 'decrease') {
                item.quantity -= 1;
                if (item.quantity <= 0) {
                    removeFromCart(id);
                    return;
                }
            }
            updateCartUI();
        }
    }

    function removeFromCart(id) {
        cart = cart.filter(item => item.id !== id);
        updateCartUI();
    }

    // User modal functionality
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

    // Open user modal
    if (userIconBtn) {
        userIconBtn.addEventListener('click', () => {
            if (userModal) { userModal.classList.remove('hidden'); }
        });
    }

    // Close modal
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            if (userModal) { userModal.classList.add('hidden'); }
        });
    }

    // Switch to registration form
    if (switchToRegisterBtn) {
        switchToRegisterBtn.addEventListener('click', (e) => {
            e.preventDefault(); // Evitar el comportamiento predeterminado del enlace
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            modalTitle.textContent = 'Regístrate';
            switchTextRegister.classList.add('hidden');
            switchTextLogin.classList.remove('hidden');
        });
    }

    // Switch to login form
    if (switchToLoginBtn) {
        switchToLoginBtn.addEventListener('click', (e) => {
            e.preventDefault(); // Evitar el comportamiento predeterminado del enlace
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
  // abrir
  if (e.target.closest('#user-icon-btn')) {
    const modal = document.getElementById('user-modal');
    if (modal) modal.classList.remove('hidden');
  }
  // cerrar
  if (e.target.closest('#close-modal')) {
    const modal = document.getElementById('user-modal');
    if (modal) modal.classList.add('hidden');
  }
});
