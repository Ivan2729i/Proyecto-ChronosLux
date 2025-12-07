
document.addEventListener("DOMContentLoaded", () => {
    // 1. Inicializar Iconos Lucide
    const lucide = window.lucide;
    if (lucide) lucide.createIcons();

    // 2. Configuración Tailwind
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
    };

    // 3. Menú Móvil
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            const menu = document.getElementById('mobile-menu');
            const icon = this.querySelector('i');
            menu.classList.toggle('hidden');

            if (menu.classList.contains('hidden')) {
                icon.setAttribute('data-lucide', 'menu');
            } else {
                icon.setAttribute('data-lucide', 'x');
            }
            if(window.lucide) window.lucide.createIcons();
        });
    }

    // 4. Modal de Usuario (Login/Registro)
    const userIconBtn = document.getElementById('user-icon-btn');
    const userModal = document.getElementById('user-modal');
    const closeModal = document.getElementById('close-modal');

    // Switch de formularios
    const switchToRegisterBtn = document.querySelector('#switch-to-register a');
    const switchToLoginBtn = document.querySelector('#switch-to-login a');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const modalTitle = document.getElementById('modal-title');
    const switchTextLogin = document.getElementById('switch-to-login');
    const switchTextRegister = document.getElementById('switch-to-register');

    if (userIconBtn && userModal) {
        userIconBtn.addEventListener('click', () => userModal.classList.remove('hidden'));
    }
    if (closeModal && userModal) {
        closeModal.addEventListener('click', () => userModal.classList.add('hidden'));
    }

    if (switchToRegisterBtn) {
        switchToRegisterBtn.addEventListener('click', (e) => {
            e.preventDefault();
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            if(modalTitle) modalTitle.textContent = 'Regístrate';
            if(switchTextRegister) switchTextRegister.classList.add('hidden');
            if(switchTextLogin) switchTextLogin.classList.remove('hidden');
        });
    }

    if (switchToLoginBtn) {
        switchToLoginBtn.addEventListener('click', (e) => {
            e.preventDefault();
            registerForm.classList.add('hidden');
            loginForm.classList.remove('hidden');
            if(modalTitle) modalTitle.textContent = 'Iniciar sesión';
            if(switchTextLogin) switchTextLogin.classList.add('hidden');
            if(switchTextRegister) switchTextRegister.classList.remove('hidden');
        });
    }

    // 5. Estrellas / Reseñas (Lógica visual)
    const starRatingContainer = document.getElementById('star-rating');
    if (starRatingContainer) {
        const ratingInput = document.getElementById('id_calificacion');
        const paintStars = (rating) => {
            const stars = starRatingContainer.querySelectorAll('[data-lucide="star"]');
            stars.forEach(star => {
                if (parseInt(star.dataset.value) <= rating) {
                    star.classList.add('fill-yellow-400', 'text-yellow-400');
                    star.classList.remove('text-gray-300');
                } else {
                    star.classList.remove('fill-yellow-400', 'text-yellow-400');
                    star.classList.add('text-gray-300');
                }
            });
        };
        starRatingContainer.addEventListener('click', (e) => {
            const star = e.target.closest('[data-lucide="star"]');
            if(star) {
                if(ratingInput) ratingInput.value = star.dataset.value;
                paintStars(star.dataset.value);
            }
        });
        starRatingContainer.addEventListener('mouseover', (e) => {
            const star = e.target.closest('[data-lucide="star"]');
            if(star) paintStars(star.dataset.value);
        });
        starRatingContainer.addEventListener('mouseout', () => {
            if(ratingInput) paintStars(ratingInput.value || 0);
        });
        if(ratingInput) paintStars(ratingInput.value || 0);
    }
});

// --- UTILERÍAS GLOBALES ---
// Definimos getCookie fuera para que cart.js y chatbot.js puedan usarla
window.getCookie = function(name) {
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
};

// Fallback robusto para cerrar modales
document.addEventListener('click', (e) => {
  if (e.target.closest('#close-modal')) {
      const m = document.getElementById('user-modal');
      if(m) m.classList.add('hidden');
  }
});