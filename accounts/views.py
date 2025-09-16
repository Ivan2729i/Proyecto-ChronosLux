from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

from .forms import EmailAuthenticationForm, SignupForm
from watches.views import build_home_context

User = get_user_model()

class HomeLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    authentication_form = EmailAuthenticationForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Portada detrás
        ctx.update(build_home_context())

        if 'form' in ctx:
            ctx['login_form'] = ctx['form']
        else:
            ctx['login_form'] = EmailAuthenticationForm(self.request)
        ctx['signup_form'] = SignupForm()

        # Bandera para abrir modal en pestaña login
        ctx['open_auth_modal'] = True
        ctx['auth_active_tab'] = 'login'
        return ctx

    def form_invalid(self, form):
        # Muy importante: pasar el form con errores como login_form
        ctx = self.get_context_data(form=form)
        ctx['login_form'] = form
        ctx['open_auth_modal'] = True
        ctx['auth_active_tab'] = 'login'
        return self.render_to_response(ctx)


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Autogenerar username a partir del email si aplica
            if hasattr(user, 'username') and hasattr(user, 'email') and user.email:
                user.username = (user.email.split('@')[0])[:150]
            user.save()
            login(request, user)
            return redirect('home')

        # POST inválido: usar form LIGADO con errores como signup_form
        ctx = build_home_context()
        ctx['signup_form'] = form
        ctx['login_form'] = EmailAuthenticationForm(request)
        ctx['open_auth_modal'] = True
        ctx['auth_active_tab'] = 'signup'
        return render(request, 'registration/signup.html', ctx)

    # GET normal: formularios limpios
    ctx = build_home_context()
    ctx['signup_form'] = SignupForm()
    ctx['login_form'] = EmailAuthenticationForm(request)
    ctx['open_auth_modal'] = True
    ctx['auth_active_tab'] = 'signup'
    return render(request, 'registration/signup.html', ctx)
