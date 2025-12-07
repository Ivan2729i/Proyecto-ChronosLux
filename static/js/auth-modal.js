
(function () {
  const userModal   = document.getElementById('user-modal');
  const loginPane   = document.getElementById('login-form-pane');
  const signupPane  = document.getElementById('signup-form-pane');
  const profilePane = document.getElementById('profile-pane');
  const titleEl     = document.getElementById('auth-modal-title');
  const backdrop    = document.getElementById('auth-backdrop');
  const dialog      = document.getElementById('auth-dialog');

  const switchToRegisterLink = document.querySelector('#switch-to-register a, a#switch-to-register, button#switch-to-register');
  const switchToLoginLink    = document.querySelector('#switch-to-login a, a#switch-to-login, button#switch-to-login');

  const userIconBtn = document.getElementById('user-icon-btn');
  const closeModal  = document.getElementById('close-modal');

  function setTitle(tab) {
    if (!titleEl) return;
    if (profilePane) { titleEl.textContent = 'Mi cuenta'; return; }
    titleEl.textContent = (tab === 'signup') ? 'Registro' : 'Inicio de sesión';
  }

  function showTab(tab) {
    if (profilePane) {
      profilePane.classList.remove('hidden');
      if (loginPane)  loginPane.classList.add('hidden');
      if (signupPane) signupPane.classList.add('hidden');
      setTitle('profile');
      return;
    }
    if (loginPane && signupPane) {
      if (tab === 'signup') { signupPane.classList.remove('hidden'); loginPane.classList.add('hidden'); }
      else { loginPane.classList.remove('hidden'); signupPane.classList.add('hidden'); }
    }
    setTitle(tab);
  }

  function openAuthModal(tab = 'login') {
    if (userModal) userModal.classList.remove('hidden');
    showTab(tab);
    document.documentElement.classList.add('overflow-y-hidden');
    document.body.classList.add('overflow-y-hidden');
  }
  function closeAuthModal() {
    if (userModal) userModal.classList.add('hidden');
    document.documentElement.classList.remove('overflow-y-hidden');
    document.body.classList.remove('overflow-y-hidden');
  }

  // Alternar pestañas
  if (switchToRegisterLink) switchToRegisterLink.addEventListener('click', e => { e.preventDefault(); openAuthModal('signup'); });
  if (switchToLoginLink)    switchToLoginLink.addEventListener('click', e => { e.preventDefault(); openAuthModal('login');  });

  // Abrir/cerrar
  if (userIconBtn) userIconBtn.addEventListener('click', () => openAuthModal(profilePane ? 'profile' : 'login'));
  if (closeModal)  closeModal.addEventListener('click', () => closeAuthModal());

  // Cerrar haciendo click en el fondo oscuro
  if (backdrop) backdrop.addEventListener('click', closeAuthModal);

  if (userModal && dialog) {
    userModal.addEventListener('click', (e) => {
      if (!dialog.contains(e.target)) closeAuthModal();
    });
    dialog.addEventListener('click', (e) => e.stopPropagation());
  }

  // Cerrar con ESC
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAuthModal(); });

  // Bandera del servidor (errores, abrir en login/signup)
  const serverFlag = window.__AUTH_MODAL__;
  if (serverFlag && serverFlag.open) {
    openAuthModal(profilePane ? 'profile' : (serverFlag.tab === 'signup' ? 'signup' : 'login'));
  }
})();
