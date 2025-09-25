from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from watches.models import Domicilio, Pedido, DetallesPedido , Devolucion
from .forms import EmailAuthenticationForm, SignupForm
from watches.views import build_home_context
from django.contrib.auth.decorators import login_required
from .forms import DomicilioForm
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages



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


# --- INICIO: LÓGICA COMPLETA DE REGISTRO DOMICILIOS ---

@login_required
def domicilio_list(request):
    # Buscamos solo los domicilios que pertenecen al usuario actual
    domicilios = Domicilio.objects.filter(usuario=request.user)

    context = {
        'domicilios': domicilios
    }
    return render(request, 'home/domicilio_list.html', context)


@login_required
def domicilio_create(request):
    if request.method == 'POST':
        form = DomicilioForm(request.POST)
        if form.is_valid():
            # Guardamos el formulario pero sin commit para poder modificarlo
            domicilio = form.save(commit=False)
            # Asignamos el usuario actual al campo 'usuario' del domicilio
            domicilio.usuario = request.user
            domicilio.save()  # Ahora sí, guardamos en la base de datos
            return redirect('domicilio_list')  # Redirigimos a la lista de domicilios
    else:
        form = DomicilioForm()

    context = {
        'form': form
    }
    return render(request, 'home/domicilio_form.html', context)

@login_required
def domicilio_edit(request, domicilio_id):
    # Busca el domicilio específico, asegurándo de que le pertenezca al usuario actual
    domicilio = get_object_or_404(Domicilio, pk=domicilio_id, usuario=request.user)

    if request.method == 'POST':
        form = DomicilioForm(request.POST, instance=domicilio)
        if form.is_valid():
            form.save()
            return redirect('domicilio_list')  # Redirige a la lista de domicilios
    else:
        # Muestra el formulario con los datos actuales del domicilio
        form = DomicilioForm(instance=domicilio)

    context = {
        'form': form
    }
    return render(request, 'home/domicilio_form.html', context)

@login_required
def domicilio_delete(request, domicilio_id):
    domicilio = get_object_or_404(Domicilio, pk=domicilio_id, usuario=request.user)

    if request.method == 'POST':
        domicilio.delete()
        return redirect('domicilio_list')

    context = {
        'domicilio': domicilio
    }
    return render(request, 'home/domicilio_delete_confirm.html', context)

# --- INICIO: LÓGICA COMPLETA DE MIS PRODUCTOS ---

@login_required
def mis_compras(request):
    # Buscamos todos los pedidos del usuario actual, ordenados del más reciente al más antiguo
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha')

    # Calculamos la fecha límite para devoluciones (hoy menos 90 días)
    fecha_limite_devolucion = timezone.now() - timedelta(days=90)

    context = {
        'pedidos': pedidos,
        'fecha_limite_devolucion': fecha_limite_devolucion
    }
    return render(request, 'compras/mis_compras.html', context)


@login_required
def solicitar_devolucion(request, pedido_id):
    # Buscamos el pedido, asegurándonos que le pertenezca al usuario actual
    pedido = get_object_or_404(Pedido, pk=pedido_id, usuario=request.user)

    # Verificamos si el pedido todavía está dentro del periodo de 90 días para devolución
    fecha_limite = pedido.fecha + timedelta(days=90)
    if timezone.now() > fecha_limite:
        messages.error(request, 'Este pedido ya no se encuentra dentro del periodo para solicitar una devolución.')
        return redirect('mis_compras')

    if request.method == 'POST':
        # Obtenemos la lista de IDs de los detalles del pedido que el usuario seleccionó
        detalles_ids_a_devolver = request.POST.getlist('detalles_a_devolver')
        motivo = request.POST.get('motivo_devolucion', '').strip()

        if not detalles_ids_a_devolver:
            messages.error(request, 'Debes seleccionar al menos un producto para devolver.')
        elif not motivo:
            messages.error(request, 'Debes escribir un motivo para la devolución.')
        else:
            # Creamos la devolución principal
            devolucion = Devolucion.objects.create(
                pedido=pedido,
                descripcion_devolucion=motivo,
                fecha_devolucion=timezone.now()
            )

            # (Aquí en el futuro se asociarían los productos devueltos a la devolución)
            # Por ahora, con esto es suficiente para el flujo básico.
            #Poner img a las devoluciones y crear tabla de imgdevoluciones
            #mejorar formulario con opciones comunes y otros

            messages.success(request, f'Tu solicitud de devolución para el pedido #{pedido.id} ha sido enviada.')
            return redirect('mis_compras')  # Redirigimos de vuelta al historial

    context = {
        'pedido': pedido
    }
    return render(request, 'compras/solicitar_devolucion.html', context)

# --- FIN: LÓGICA COMPLETA DE MIS PRODUCTOS ---

# --- INICIO: LÓGICA COMPLETA DE MIS DEVOLUCIONES ---

@login_required
def mis_devoluciones(request):
    # Buscamos todas las devoluciones asociadas al usuario actual
    devoluciones = Devolucion.objects.filter(pedido__usuario=request.user).order_by('-fecha_devolucion')

    context = {
        'devoluciones': devoluciones
    }
    return render(request, 'compras/mis_devoluciones.html', context)