
document.addEventListener("DOMContentLoaded", () => {

    // --- 1. UTILIDADES DE URL ---
    const getQuery = () => new URLSearchParams(window.location.search);

    const setQueryAndReload = (params) => {
        const url = new URL(window.location.href);
        const q = getQuery();

        // Limpiar o establecer parámetros
        Object.entries(params).forEach(([k, v]) => {
            if (v === null || v === undefined || v === "" || v === "all") {
                q.delete(k);
            } else {
                q.set(k, v);
            }
        });

        // Al cambiar filtros, reiniciar paginación
        q.delete('page');

        url.search = q.toString();
        window.location.href = url.toString();
    };

    // --- 2. FAVORITOS INSTANTÁNEOS (OPTIMISTIC UI) ---
    const bindFavoriteToggles = () => {
        // Obtener CSRF Token de las cookies
        const getCsrf = () => {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const c = cookies[i].trim();
                    if (c.substring(0, 10) === ('csrftoken=')) {
                        cookieValue = decodeURIComponent(c.substring(10));
                        break;
                    }
                }
            }
            return cookieValue;
        };

        document.body.addEventListener("click", async (e) => {
            const btn = e.target.closest(".fav-toggle");
            if (!btn) return;

            e.preventDefault();
            e.stopPropagation();

            // Verificar autenticación global
            const userIsAuthenticated = document.body.dataset.isAuthenticated === 'true';

            if (!userIsAuthenticated) {
                // Abrir modal de login
                const userIcon = document.getElementById('user-icon-btn');
                if(userIcon) userIcon.click();
                return;
            }

            const watchId = btn.dataset.watchId;
            const icon = btn.querySelector('[data-lucide="heart"]');

            // --- VELOCIDAD: Cambiar visualmente PRIMERO ---
            const wasActive = btn.dataset.active === "1";

            if (!wasActive) {
                // Activar visualmente
                icon.classList.add("fill-current", "text-rose-500");
                icon.classList.remove("text-gray-600");
                btn.dataset.active = "1";
            } else {
                // Desactivar visualmente
                icon.classList.remove("fill-current", "text-rose-500");
                icon.classList.add("text-gray-600");
                btn.dataset.active = "0";
            }

            // Enviar petición en segundo plano
            try {
                const url = `/favoritos/toggle/${watchId}/`;
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrf(),
                        'Content-Type': 'application/json'
                    }
                });
                const data = await response.json();

                // Si falló el servidor, revertir el cambio visual
                if (data.status !== 'ok') {
                    console.error("Error servidor, revirtiendo...");
                    // Aquí podrías revertir las clases si es crítico
                }
            } catch (error) {
                console.error("Error de red:", error);
            }
        });
    };

    // --- 3. FILTROS (DROPDOWNS Y SELECTS) ---
    const bindFilters = () => {
        // A) Selects nativos
        const selects = document.querySelectorAll('select[data-param]');
        selects.forEach(sel => {
            sel.addEventListener('change', (e) => {
                setQueryAndReload({ [sel.dataset.param]: sel.value });
            });
        });

        // B) Dropdowns personalizados
        document.addEventListener('click', (e) => {
            const toggle = e.target.closest('.dd-toggle');
            const option = e.target.closest('.dd-option');

            // Selección de opción
            if (option) {
                const param = option.dataset.param;
                const value = option.dataset.value;
                setQueryAndReload({ [param]: value });
                return;
            }

            // Cerrar si clic fuera
            if (!e.target.closest('.dd')) {
                document.querySelectorAll('.dd-menu').forEach(m => m.classList.add('hidden'));
                return;
            }

            // Abrir/Cerrar menú
            if (toggle) {
                const dd = toggle.closest('.dd');
                const menu = dd.querySelector('.dd-menu');
                const wasHidden = menu.classList.contains('hidden');

                // Cerrar todos los demás
                document.querySelectorAll('.dd-menu').forEach(m => m.classList.add('hidden'));

                if (wasHidden) {
                    menu.classList.remove('hidden');
                }
            }
        });
    };

    // --- 4. PAGINACIÓN (Mantener filtros) ---
    const patchPaginationLinks = () => {
        const links = document.querySelectorAll(".pagination a, .paginator a");
        const currentParams = getQuery();

        links.forEach((a) => {
            try {
                const url = new URL(a.href, window.location.origin);
                currentParams.forEach((val, key) => {
                    if (!url.searchParams.has(key) && key !== 'page') {
                        url.searchParams.set(key, val);
                    }
                });
                a.href = url.toString();
            } catch (err) {}
        });
    };

    // --- INICIALIZAR ---
    bindFavoriteToggles();
    bindFilters();
    patchPaginationLinks();

    if (window.lucide) window.lucide.createIcons();
});