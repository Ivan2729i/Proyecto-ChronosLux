from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from watches.models import Domicilio, Pedido, DetallesPedido , Devolucion, Producto, Marca, Favorito
from .forms import EmailAuthenticationForm, SignupForm
from django.contrib.auth.decorators import login_required
from .forms import DomicilioForm
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
import uuid
import os
from watches.context_processors import home_page_context



User = get_user_model()

# --- INICIO: LÓGICA COMPLETA DE LA VISTA DE HOME ---

class HomeLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    authentication_form = EmailAuthenticationForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Portada detrás
        ctx.update(home_page_context(self.request))

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
        ctx = home_page_context(request)
        ctx['signup_form'] = form
        ctx['login_form'] = EmailAuthenticationForm(request)
        ctx['open_auth_modal'] = True
        ctx['auth_active_tab'] = 'signup'
        return render(request, 'registration/signup.html', ctx)

    # GET normal: formularios limpios
    ctx = home_page_context(request)
    ctx['signup_form'] = SignupForm()
    ctx['login_form'] = EmailAuthenticationForm(request)
    ctx['open_auth_modal'] = True
    ctx['auth_active_tab'] = 'signup'
    return render(request, 'registration/signup.html', ctx)

# --- FIN: LÓGICA COMPLETA DE LA VISTA DE HOME ---

# --- INICIO: LÓGICA COMPLETA DE REGISTRO DOMICILIOS ---

@login_required
def domicilio_list(request):
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
            domicilio = form.save(commit=False)
            domicilio.usuario = request.user
            domicilio.save()
            return redirect('domicilio_list')
    else:
        form = DomicilioForm()

    context = {
        'form': form
    }
    return render(request, 'home/domicilio_form.html', context)

@login_required
def domicilio_edit(request, domicilio_id):
    domicilio = get_object_or_404(Domicilio, pk=domicilio_id, usuario=request.user)

    if request.method == 'POST':
        form = DomicilioForm(request.POST, instance=domicilio)
        if form.is_valid():
            form.save()
            return redirect('domicilio_list')
    else:
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

# --- FIN: LÓGICA COMPLETA DE REGISTRO DOMICILIOS ---

# --- INICIO: LÓGICA COMPLETA DE MIS COMPRAS ---

@login_required
def mis_compras(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha')

    pedidos_con_devolucion = Devolucion.objects.filter(pedido__in=pedidos).values_list('pedido_id', flat=True)

    fecha_limite_devolucion = timezone.now() - timedelta(days=90)

    context = {
        'pedidos': pedidos,
        'fecha_limite_devolucion': fecha_limite_devolucion,
        'pedidos_con_devolucion': list(pedidos_con_devolucion)
    }
    return render(request, 'compras/mis_compras.html', context)

@login_required
def solicitar_devolucion(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id, usuario=request.user)

    fecha_limite = pedido.fecha + timedelta(days=90)
    if timezone.now() > fecha_limite:
        messages.error(request, 'Este pedido ya no se encuentra dentro del periodo para solicitar una devolución.')
        return redirect('mis_compras')

    if request.method == 'POST':
        detalles_ids_a_devolver = request.POST.getlist('detalles_a_devolver')
        motivo = request.POST.get('motivo_devolucion', '').strip()
        imagen_devolucion = request.FILES.get('imagen_devolucion')

        if not detalles_ids_a_devolver:
            messages.error(request, 'Debes seleccionar al menos un producto para devolver.')
        elif not motivo:
            messages.error(request, 'Debes escribir un motivo para la devolución.')
        else:
            # Creamos la devolución
            devolucion = Devolucion(
                pedido=pedido,
                descripcion_devolucion=motivo,
                fecha_devolucion=timezone.now()
            )

            if imagen_devolucion:
                # Generamos un nombre de archivo único para evitar colisiones
                extension = os.path.splitext(imagen_devolucion.name)[1]
                nombre_unico = f"{uuid.uuid4()}{extension}"
                imagen_devolucion.name = nombre_unico
                devolucion.url_img_prod_devuelto = imagen_devolucion

            devolucion.save()

            messages.success(request, f'Tu solicitud de devolución para el pedido #{pedido.id} ha sido enviada.')
            return redirect('mis_compras')

    context = {
        'pedido': pedido
    }
    return render(request, 'compras/solicitar_devolucion.html', context)

# --- FIN: LÓGICA COMPLETA DE MIS COMPRAS ---

# --- INICIO: LÓGICA COMPLETA DE MIS DEVOLUCIONES ---

@login_required
def mis_devoluciones(request):
    # Buscamos todas las devoluciones asociadas al usuario actual
    devoluciones = Devolucion.objects.filter(pedido__usuario=request.user).order_by('-fecha_devolucion')

    context = {
        'devoluciones': devoluciones
    }
    return render(request, 'compras/mis_devoluciones.html', context)

# --- FIN: LÓGICA COMPLETA DE MIS DEVOLUCIONES ---