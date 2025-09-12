// Main JavaScript functionality
document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide icons
  const lucide = window.lucide; // Declare the lucide variable
  if (typeof lucide !== "undefined") {
    lucide.createIcons();
  }
});

// Tailwind configuration
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: '#1e3a8a',
                'primary-foreground': '#ffffff',
                secondary: '#d4af37',
                'secondary-foreground': '#1e3a8a',
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
<<<<<<< HEAD

// Initialize Lucide icons
    lucide.createIcons();

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

    // Cart modal
    document.getElementById('cart-btn').addEventListener('click', function() {
        document.getElementById('cart-modal').classList.remove('hidden');
    });

    document.getElementById('close-cart').addEventListener('click', function() {
        document.getElementById('cart-modal').classList.add('hidden');
    });

    // Add to cart functionality
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

    // Filter functionality
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;

            // Update active button
            document.querySelectorAll('.filter-btn').forEach(b => {
                b.classList.remove('active', 'bg-primary', 'text-primary-foreground');
                b.classList.add('text-primary', 'hover:bg-primary', 'hover:text-primary-foreground');
            });

            this.classList.add('active', 'bg-primary', 'text-primary-foreground');
            this.classList.remove('text-primary', 'hover:bg-primary', 'hover:text-primary-foreground');

            // Filter watches
            document.querySelectorAll('.watch-item').forEach(item => {
                if (filter === 'all' || item.dataset.brand === filter) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
=======
>>>>>>> 9cc1c6076f5768c7ed82c704e561d0b36d73e543
