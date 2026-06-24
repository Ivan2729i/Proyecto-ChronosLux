/* cart.js - Lógica del carrito de compras */

document.addEventListener("DOMContentLoaded", () => {

    // Función visual para el ícono del nav
    function updateCartIcon(total_items) {
        const cartCount = document.getElementById('cart-count');
        if (!cartCount) return;

        // Pequeña animación
        cartCount.style.transform = "scale(1.2)";
        setTimeout(() => cartCount.style.transform = "scale(1)", 200);

        if (total_items > 0) {
            cartCount.textContent = total_items;
            cartCount.classList.remove('hidden');
        } else {
            cartCount.textContent = '0';
            cartCount.classList.add('hidden');
        }
    }

    // Renderizado del modal
    async function renderCartModal() {
        const cartItemsContainer = document.getElementById('cart-items');
        const cartTotalEl = document.getElementById('cart-total');
        const checkoutBtn = document.getElementById('checkout-btn');

        if (!cartItemsContainer) return;

        // Mostrar "Cargando..."
        cartItemsContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center h-40 space-y-3">
                <i data-lucide="loader-2" class="w-8 h-8 animate-spin text-yellow-600"></i>
                <p class="text-gray-500 text-sm font-medium">Cargando tu carrito...</p>
            </div>
        `;
        if(window.lucide) window.lucide.createIcons();

        try {
            const response = await fetch('/api/carrito/');
            const data = await response.json();

            if (!cartTotalEl || !checkoutBtn) return;

            cartItemsContainer.innerHTML = '';

            if (data.cart_items.length === 0) {
                cartItemsContainer.innerHTML = `
                    <div class="flex flex-col items-center justify-center py-10 text-gray-500">
                        <i data-lucide="shopping-bag" class="w-10 h-10 mb-3 opacity-50"></i>
                        <p>Tu carrito está vacío</p>
                    </div>
                `;
                checkoutBtn.classList.add('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
            } else {
                data.cart_items.forEach(item => {
                    // --- AQUÍ ESTÁ EL CAMBIO VISUAL (INPUT EN VEZ DE SPAN) ---
                    const itemHTML = `
                        <div class="flex items-center space-x-4 mb-4 p-4 border rounded-lg bg-white shadow-sm">
                            <img src="/media/${item.image_url}" alt="${item.name}" class="w-16 h-16 object-cover rounded">
                            <div class="flex-1">
                                <h3 class="font-semibold text-sm md:text-base">${item.brand} ${item.name}</h3>
                                <p class="text-gray-600 font-mono text-sm">$${item.price.toFixed(2)}</p>
                                <div class="flex items-center space-x-2 mt-2">
                                    <button class="quantity-btn w-8 h-8 flex items-center justify-center border rounded hover:bg-gray-100 transition-colors" data-id="${item.id}" data-action="decrease">-</button>

                                    <input type="number"
                                           min="1"
                                           value="${item.quantity}"
                                           data-id="${item.id}"
                                           class="manual-quantity-input w-12 text-center border rounded mx-1 p-1 text-sm font-semibold focus:outline-none focus:border-blue-500"
                                    >

                                    <button class="quantity-btn w-8 h-8 flex items-center justify-center border rounded hover:bg-gray-100 transition-colors" data-id="${item.id}" data-action="increase">+</button>
                                    <button class="remove-btn ml-auto text-red-500 text-sm hover:text-red-700 font-semibold transition-colors" data-id="${item.id}">
                                        <i data-lucide="trash-2" class="w-4 h-4"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                    cartItemsContainer.innerHTML += itemHTML;
                });
                checkoutBtn.classList.remove('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
                if(window.lucide) window.lucide.createIcons();
            }

            cartTotalEl.textContent = `$${data.total_price.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            updateCartIcon(data.total_items);

        } catch (error) {
            console.error("Error al renderizar carrito:", error);
            cartItemsContainer.innerHTML = '<p class="text-red-500 text-center py-4">Error al cargar el carrito.</p>';
        }
    }

    // --- 1. LISTENER DE CLICS (Botones +, -, Eliminar, Abrir/Cerrar) ---
    document.body.addEventListener('click', async function(event) {
        const button = event.target.closest('button');

        // Abrir modal
        if (event.target.closest('#cart-btn')) {
            const m = document.getElementById('cart-modal');
            if(m) {
                m.classList.remove('hidden');
                renderCartModal();
            }
        }
        // Cerrar modal
        if (event.target.closest('#close-cart')) {
            document.getElementById('cart-modal')?.classList.add('hidden');
        }

        if (!button) return;

        const csrftoken = window.getCookie('csrftoken');

        // Agregar al carrito (Catálogo)
        if (button.matches('.add-to-cart')) {
            event.preventDefault();
            const watchId = button.dataset.watchId;
            const url = `/carrito/agregar/${watchId}/`;

            const originalHTML = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<div class="flex items-center gap-2"><i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> <span>...</span></div>';
            button.classList.add('opacity-75');
            if(window.lucide) window.lucide.createIcons();

            try {
                const response = await fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrftoken } });
                const data = await response.json();
                if (data.status === 'ok') {
                    updateCartIcon(data.total_items);
                    button.innerHTML = '¡Listo!';
                    setTimeout(() => {
                        button.innerHTML = originalHTML;
                        button.disabled = false;
                        button.classList.remove('opacity-75');
                    }, 1000);
                }
            } catch (e) {
                button.innerHTML = originalHTML;
                button.disabled = false;
            }
        }

        // Eliminar del carrito
        if (button.matches('.remove-btn')) {
            const watchId = button.dataset.id;
            button.closest('.flex').style.opacity = '0.3';
            const url = `/carrito/eliminar/${watchId}/`;
            const response = await fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrftoken } });
            if ((await response.json()).status === 'ok') renderCartModal();
        }

        // Botones + y - (Cantidad)
        if (button.matches('.quantity-btn')) {
            const watchId = button.dataset.id;
            const action = button.dataset.action;
            const url = `/carrito/actualizar/${watchId}/`;

            const container = button.parentElement;
            container.querySelectorAll('button, input').forEach(el => el.disabled = true); // Bloqueamos todo

            const response = await fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: action })
            });
            if ((await response.json()).status === 'ok') renderCartModal();
        }
    });

    // --- 2. LISTENER DE CAMBIOS (INPUT MANUAL) ---
    // Este detecta cuando escribes un número y das Enter o sales de la casilla
    document.body.addEventListener('change', async function(event) {
        if (event.target.matches('.manual-quantity-input')) {
            const input = event.target;
            const watchId = input.dataset.id;
            let newQuantity = parseInt(input.value);
            const csrftoken = window.getCookie('csrftoken');

            // PROTECCIÓN: Si es inválido o menor a 1, forzamos a 1
            if (newQuantity < 1 || isNaN(newQuantity)) {
                newQuantity = 1;
            }

            // Deshabilitar input visualmente mientras carga
            input.disabled = true;
            input.classList.add('opacity-50');

            const url = `/carrito/actualizar/${watchId}/`;

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        action: 'manual',
                        quantity: newQuantity
                    })
                });

                if ((await response.json()).status === 'ok') {
                    renderCartModal(); // Recargar carrito con nuevos totales
                }
            } catch (error) {
                console.error('Error actualizando cantidad', error);
                input.disabled = false;
            }
        }
    });
});