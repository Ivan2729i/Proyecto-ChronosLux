from .forms import EmailAuthenticationForm, SignupForm

def auth_forms(request):
    return {
        "login_form": EmailAuthenticationForm(request),
        "signup_form": SignupForm(),
    }


def user_roles_context(request):
    is_proveedor = False

    if request.user.is_authenticated:
        pertenece_grupo = request.user.groups.filter(name='Proveedores').exists()

        try:
            from proveedores.models import Proveedor
            tiene_perfil_proveedor = Proveedor.objects.filter(user=request.user).exists()
        except Exception:
            tiene_perfil_proveedor = False

        is_proveedor = pertenece_grupo or tiene_perfil_proveedor

    return {
        'is_proveedor': is_proveedor
    }