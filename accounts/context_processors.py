from .forms import EmailAuthenticationForm, SignupForm

def auth_forms(request):
    return {
        "login_form": EmailAuthenticationForm(request),
        "signup_form": SignupForm(),
    }


def user_roles_context(request):
    is_proveedor = False
    if request.user.is_authenticated:
        is_proveedor = request.user.groups.filter(name='Proveedores').exists()

    return {
        'is_proveedor': is_proveedor
    }