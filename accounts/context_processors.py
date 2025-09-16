from .forms import EmailAuthenticationForm, SignupForm

def auth_forms(request):
    return {
        "login_form": EmailAuthenticationForm(request),
        "signup_form": SignupForm(),
    }
