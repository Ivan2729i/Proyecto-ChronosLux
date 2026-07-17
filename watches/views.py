import os
import uuid, re
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Producto, Categoria, Resena, ImgProducto, Marca, Domicilio, DetallesPedido, Pedido, Envio, Pago, Favorito, Carrito, DetalleCarrito, Devolucion
from django.http import JsonResponse, StreamingHttpResponse, Http404
from django.core.exceptions import ValidationError
import json
from .forms import ProductoForm, ResenaForm
from django.db.models import Q, Sum
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.contrib.admin.views.decorators import staff_member_required
from .context_processors import home_page_context
from django.db.models import Case, When, Value, IntegerField
from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from openai import OpenAI, RateLimitError, APIError
from watches.models import Producto



def get_object_or_404_mongo(model_or_queryset, **kwargs):
    try:
        return get_object_or_404(model_or_queryset, **kwargs)
    except ValidationError:
        raise Http404("ID no válido")

# --- INICIO: LÓGICA COMPLETA DE LA VISTA DE HOME ---

def home(request):
    context = home_page_context(request)
    return render(request, 'home.html', context)

# --- FIN: LÓGICA COMPLETA DE LA VISTA DE HOME ---

# --- INICIO: LÓGICA COMPLETA DE VISTA Y FILTROS NORMALES ---

def catalog(request):
    items = Producto.objects.select_related('categoria', 'marca', 'imgproducto')

    # Barra de busqueda
    query = request.GET.get('q')
    if query:
        items = items.filter(
            Q(nombre__icontains=query) |
            Q(marca__nombre__icontains=query) |
            Q(descripcion1__icontains=query) |
            Q(descripcion2__icontains=query) |
            Q(descripcion3__icontains=query) |
            Q(categoria__material__icontains=query) |
            Q(categoria__genero__icontains=query) |
            Q(categoria__tipo__icontains=query)
        )
    else:
        items = items.filter(es_exclusivo=False)

    # Filtros
    t = (request.GET.get('type') or '').lower()
    price = (request.GET.get('price') or '').lower()
    gender = (request.GET.get('gender') or '').lower()
    marca_filtro = (request.GET.get('brand') or '').lower()

    # Funciones de filtro
    def match_type(x):
        if not t or t == 'all': return True
        value = (x.categoria.tipo or '').lower()
        return value == t

    def match_price(x):
        if not price or price == 'all': return True
        p = float(x.precio)
        if price == 'up_to_5000': return p <= 5000
        if price == '5000_10000': return 5000 <= p <= 10000
        if price == 'over_10000': return p > 10000
        return True

    def match_gender(x):
        if not gender or gender == 'all': return True
        return (x.categoria.genero or '').lower() == gender

    def match_brand(x):
        if not marca_filtro or marca_filtro == 'all': return True
        return (x.marca.nombre or '').lower() == marca_filtro

    # Aplicar filtros
    items = [x for x in items if match_type(x) and match_price(x) and match_gender(x) and match_brand(x)]

    # Ordenamiento
    sort = (request.GET.get('sort') or 'featured').lower()
    if sort == 'price_asc':
        items = sorted(items, key=lambda x: x.precio)
    elif sort == 'price_desc':
        items = sorted(items, key=lambda x: x.precio, reverse=True)
    elif sort == 'name_asc':
        items = sorted(items, key=lambda x: x.nombre)

    favoritos_ids = []

    if request.user.is_authenticated:
        favoritos_ids = list(
            Favorito.objects.filter(
                usuario=request.user
            ).values_list('producto_id', flat=True)
        )

    tipos_disponibles = Categoria.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
    generos_disponibles = Categoria.objects.values_list('genero', flat=True).distinct().order_by('genero')
    marcas_disponibles = Marca.objects.all().order_by('nombre')

    return render(request, 'catalog.html', {
        'catalog_watches': items,
        'querystring': request.GET.urlencode(),
        'search_query': query,
        'current': {
            'type': t or 'all',
            'price': price or 'all',
            'gender': gender or 'all',
            'sort': sort or 'featured',
            'brand': marca_filtro or 'all',
        },
        'tipos': tipos_disponibles,
        'generos': generos_disponibles,
        'marcas': marcas_disponibles,
        'favoritos_ids': favoritos_ids,
    })


def product_detail(request, producto_id):
    producto = get_object_or_404_mongo(
        Producto.objects.select_related('categoria', 'marca', 'imgproducto'),
        pk=producto_id
    )

    mi_resena = None
    # Lógica del formulario de reseña
    if request.user.is_authenticated:
        mi_resena = Resena.objects.filter(producto=producto, usuario=request.user).first()
        if request.method == 'POST':
            form = ResenaForm(request.POST, instance=mi_resena)
            if form.is_valid():
                resena = form.save(commit=False)
                resena.usuario = request.user
                resena.producto = producto
                resena.fecha = timezone.now()
                resena.save()
                return redirect('product_detail', producto_id=producto.id)
        else:
            form = ResenaForm(instance=mi_resena)
    else:
        form = ResenaForm()

    if request.user.is_authenticated:
        todas_las_resenas = Resena.objects.filter(producto=producto).annotate(
            es_mi_resena=Case(
                When(usuario=request.user, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-es_mi_resena', '-fecha')
    else:
        todas_las_resenas = Resena.objects.filter(producto=producto).order_by('-fecha')

    # Lógica para elegir la plantilla
    if producto.es_exclusivo:
        template_name = 'catalog/exclusive_product_detail.html'
    else:
        template_name = 'catalog/product_detail.html'

    context = {
        'producto': producto,
        'reseñas': todas_las_resenas,
        'mi_resena': mi_resena,
        'resena_form': form,
    }
    return render(request, template_name, context)

# --- FIN: LÓGICA COMPLETA DE VISTA Y FILTROS NORMALES ---

# --- INICIO: LÓGICA COMPLETA DEL CARRITO ---

def _get_user_cart(request):
    if not request.user.is_authenticated:
        return None

    # Busca un carrito activo que no haya expirado.
    cart, created = Carrito.objects.get_or_create(
        usuario=request.user,
        estado='activo',
        defaults={
            'fecha_creacion': timezone.now(),
            'fecha_expiracion': timezone.now() + timedelta(minutes=60)
        }
    )

    # Si el carrito ya existía, comprueba si ha expirado.
    if not created and cart.fecha_expiracion and cart.fecha_expiracion < timezone.now():
        cart.estado = 'expirado'
        cart.save()
        cart = Carrito.objects.create(
            usuario=request.user,
            fecha_creacion=timezone.now(),
            fecha_expiracion=timezone.now() + timedelta(minutes=60)
        )
    return cart


def add_to_cart(request, producto_id):
    producto = get_object_or_404_mongo(Producto, pk=producto_id)
    total_items = 0

    if request.user.is_authenticated:
        cart = _get_user_cart(request)
        if cart:
            detalle, created = DetalleCarrito.objects.get_or_create(
                carrito=cart,
                producto=producto,
                defaults={
                    'cantidad': 1,
                    'precio_unitario': producto.precio,
                    'subtotal': producto.precio
                }
            )

            if not created:
                detalle.cantidad += 1
                detalle.subtotal = detalle.cantidad * detalle.precio_unitario
                detalle.save()

            total_items_query = DetalleCarrito.objects.filter(carrito=cart).aggregate(total=Sum('cantidad'))
            total_items = total_items_query['total'] or 0
    else:
        cart_session = request.session.get('cart', {})
        pid_str = str(producto_id)
        if pid_str in cart_session:
            cart_session[pid_str]['quantity'] += 1
        else:
            cart_session[pid_str] = {
                'quantity': 1, 'price': str(producto.precio), 'name': producto.nombre,
                'image_url': producto.imgproducto.url.name, 'brand': producto.marca.nombre
            }
        request.session['cart'] = cart_session
        total_items = sum(item['quantity'] for item in cart_session.values())

    return JsonResponse({'status': 'ok', 'total_items': total_items})

def get_cart_data(request):
    cart_items = []
    total_price = 0
    total_items = 0

    if request.user.is_authenticated:
        cart = _get_user_cart(request)
        if cart:
            detalles = DetalleCarrito.objects.filter(carrito=cart).select_related('producto__marca',
                                                                                  'producto__imgproducto')
            for item in detalles:
                cart_items.append({
                    'id': str(item.producto.id),
                    'name': item.producto.nombre,
                    'brand': item.producto.marca.nombre,
                    'quantity': item.cantidad,
                    'price': float(item.precio_unitario),
                    'image_url': item.producto.imgproducto.url.name,
                    'subtotal': float(item.subtotal)
                })
                total_price += item.subtotal
                total_items += item.cantidad
    else:
        cart_session = request.session.get('cart', {})
        for pid, item_data in cart_session.items():
            subtotal = item_data['quantity'] * float(item_data['price'])
            cart_items.append({
                'id': pid, 'name': item_data['name'], 'brand': item_data.get('brand', ''),
                'quantity': item_data['quantity'], 'price': float(item_data['price']),
                'image_url': item_data['image_url'], 'subtotal': subtotal
            })
            total_price += subtotal
            total_items += item_data['quantity']

    return JsonResponse({
        'cart_items': cart_items,
        'total_price': total_price,
        'total_items': total_items,
    })


def update_cart_quantity(request, producto_id):
    if request.method == 'POST':
        body_data = json.loads(request.body)
        action = body_data.get('action')
        new_quantity = int(body_data.get('quantity', 1))

        if request.user.is_authenticated:
            cart = _get_user_cart(request)
            detalle = get_object_or_404_mongo(DetalleCarrito, carrito=cart, producto_id=producto_id)

            if action == 'increase':
                detalle.cantidad += 1
            elif action == 'decrease':
                detalle.cantidad -= 1
            elif action == 'manual':
                detalle.cantidad = new_quantity

            if detalle.cantidad <= 0:
                detalle.delete()
            else:
                detalle.subtotal = detalle.cantidad * detalle.precio_unitario
                detalle.save()
        else:
            cart_session = request.session.get('cart', {})
            pid_str = str(producto_id)
            if pid_str in cart_session:
                if action == 'increase':
                    cart_session[pid_str]['quantity'] += 1
                elif action == 'decrease':
                    cart_session[pid_str]['quantity'] -= 1
                    if cart_session[pid_str]['quantity'] <= 0:
                        del cart_session[pid_str]
                elif action == 'manual':
                    if new_quantity <= 0:
                        del cart_session[pid_str]
                    else:
                        cart_session[pid_str]['quantity'] = new_quantity

                request.session['cart'] = cart_session

    return JsonResponse({'status': 'ok'})


def remove_from_cart(request, producto_id):
    if request.user.is_authenticated:
        cart = _get_user_cart(request)
        DetalleCarrito.objects.filter(carrito=cart, producto_id=producto_id).delete()
    else:
        cart_session = request.session.get('cart', {})
        pid_str = str(producto_id)
        if pid_str in cart_session:
            del cart_session[pid_str]
            request.session['cart'] = cart_session

    return JsonResponse({'status': 'ok'})

# --- FIN: LÓGICA COMPLETA DEL CARRITO ---

# --- INICIO: LÓGICA COMPLETA DE ADMIN ---

def admin_dashboard(request):
    productos = Producto.objects.select_related('marca').all()

    context = {
        'productos': productos
    }
    return render(request, 'admin/dashboard.html', context)


def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            # --- Lógica para buscar o crear la Categoría ---
            categoria_obj, created = Categoria.objects.get_or_create(
                genero=form.cleaned_data.get('genero'),
                material=form.cleaned_data.get('material'),
                tipo=form.cleaned_data.get('tipo')
            )

            # Guardamos el producto sin commit para asignarle la categoría
            producto = form.save(commit=False)
            producto.categoria = categoria_obj
            producto.stock = 1
            producto.save()

            # --- Lógica para guardar la imagen ---
            uploaded_image = form.cleaned_data.get('imagen')
            if uploaded_image:
                extension = os.path.splitext(uploaded_image.name)[1]
                nombre_unico = f"{uuid.uuid4()}{extension}"
                uploaded_image.name = nombre_unico

                ImgProducto.objects.create(producto=producto, url=uploaded_image)

            return redirect('admin_dashboard')
    else:
        form = ProductoForm()

    context = {'form': form}
    return render(request, 'admin/producto_form.html', context)


def editar_producto(request, producto_id):
    producto = get_object_or_404_mongo(Producto, pk=producto_id)

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            categoria_obj, created = Categoria.objects.get_or_create(
                genero=form.cleaned_data.get('genero'),
                material=form.cleaned_data.get('material'),
                tipo=form.cleaned_data.get('tipo')
            )

            edited_producto = form.save(commit=False)
            edited_producto.categoria = categoria_obj
            edited_producto.save()

            uploaded_image = form.cleaned_data.get('imagen')
            if uploaded_image:
                if producto.imgproducto:
                    producto.imgproducto.delete()

                extension = os.path.splitext(uploaded_image.name)[1]
                nombre_unico = f"{uuid.uuid4()}{extension}"
                uploaded_image.name = nombre_unico

                # Actualiza o crea la ImgProducto
                ImgProducto.objects.update_or_create(
                    producto=edited_producto,
                    defaults={'url': uploaded_image}
                )

            return redirect('admin_dashboard')
    else:
        # Si se accede por primera vez, mostramos el formulario relleno con los datos del producto
        form = ProductoForm(instance=producto, initial={
            'genero': producto.categoria.genero,
            'material': producto.categoria.material,
            'tipo': producto.categoria.tipo,
        })

    context = {
        'form': form
    }
    return render(request, 'admin/producto_form.html', context)


def eliminar_producto(request, producto_id):
    producto = get_object_or_404_mongo(Producto, pk=producto_id)

    if request.method == 'POST':
        if hasattr(producto, 'imgproducto'):
            producto.imgproducto.url.delete(save=False)

        producto.delete()

        return redirect('admin_dashboard')

    context = {
        'producto': producto
    }
    return render(request, 'admin/eliminar_producto.html', context)

# --- FIN: LÓGICA COMPLETA DE ADMIN ---

# --- INICIO: LÓGICA COMPLETA DE VISTA Y FILTROS EXCLUSIVE ---

def exclusivos_catalog(request):
    items = Producto.objects.select_related('marca', 'imgproducto', 'categoria').filter(es_exclusivo=True)

    tipo_filtro = request.GET.get('type', '').lower()
    precio_filtro = request.GET.get('price', '').lower()
    genero_filtro = request.GET.get('gender', '').lower()
    sort_order = request.GET.get('sort', 'featured').lower()
    marca_filtro = request.GET.get('brand', '').lower()

    if tipo_filtro and tipo_filtro != 'all':
        items = items.filter(categoria__tipo__iexact=tipo_filtro)
    if genero_filtro and genero_filtro != 'all':
        items = items.filter(categoria__genero__iexact=genero_filtro)
    if marca_filtro and marca_filtro != 'all':
        items = items.filter(marca__nombre__iexact=marca_filtro)
    if precio_filtro and precio_filtro != 'all':
        if precio_filtro == 'up_to_60000':
            items = items.filter(precio__lte=60000)
        elif precio_filtro == '60000_100000':
            items = items.filter(precio__gte=60000, precio__lte=100000)
        elif precio_filtro == 'over_100000':
            items = items.filter(precio__gt=100000)

    if sort_order == 'price_asc':
        items = items.order_by('precio')
    elif sort_order == 'price_desc':
        items = items.order_by('-precio')
    elif sort_order == 'name_asc':
        items = items.order_by('nombre')

    favoritos_ids = []

    if request.user.is_authenticated:
        favoritos_ids = list(
            Favorito.objects.filter(
                usuario=request.user
            ).values_list('producto_id', flat=True)
        )

    tipos_disponibles = Categoria.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
    generos_disponibles = Categoria.objects.values_list('genero', flat=True).distinct().order_by('genero')
    marcas_disponibles = Marca.objects.all().order_by('nombre')

    context = {
        'productos_exclusivos': items,
        'querystring': request.GET.urlencode(),
        'current': {
            'type': tipo_filtro or 'all',
            'price': precio_filtro or 'all',
            'gender': genero_filtro or 'all',
            'sort': sort_order or 'featured',
            'brand': marca_filtro or 'all',
        },
        'tipos': tipos_disponibles,
        'generos': generos_disponibles,
        'marcas': marcas_disponibles,
        'favoritos_ids': favoritos_ids,
    }

    return render(request, 'exclusivos_catalog.html', context)

# --- FIN: LÓGICA COMPLETA DE FILTROS EXCLUSIVE ---

# --- INICIO: LÓGICA COMPLETA DE CHECKOUT CARRITO ---

@login_required
def checkout_page(request):
    cart_items = []
    total_price = 0

    cart = _get_user_cart(request)
    if cart:
        # Obtiene todos los detalles de ese carrito
        detalles = DetalleCarrito.objects.filter(carrito=cart).select_related('producto__marca',
                                                                              'producto__imgproducto')
        for item in detalles:
            cart_items.append({
                'id': str(item.producto.id),
                'name': item.producto.nombre,
                'brand': item.producto.marca.nombre,
                'quantity': item.cantidad,
                'price': float(item.precio_unitario),
                'image_url': item.producto.imgproducto.url.name,
                'subtotal': float(item.subtotal)
            })
            total_price += item.subtotal

    # Obtiene los domicilios del usuario
    domicilios = Domicilio.objects.filter(usuario=request.user)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'domicilios': domicilios
    }

    return render(request, 'checkout.html', context)


@login_required
def place_order(request):
    if request.method != 'POST':
        return redirect('home')

    cart = _get_user_cart(request)
    domicilio_id = request.POST.get('domicilio_seleccionado')
    metodo_pago = request.POST.get('metodo_pago')

    if not cart or not cart.detallecarrito_set.exists():
        messages.error(
            request,
            'Tu carrito está vacío o ya no se encuentra disponible.'
        )
        return redirect('checkout_page')

    if not domicilio_id:
        messages.error(
            request,
            'Debes seleccionar una dirección de envío.'
        )
        return redirect('checkout_page')

    metodos_validos = {
        'tarjeta_credito',
        'tarjeta_debito',
        'paypal'
    }

    if metodo_pago not in metodos_validos:
        messages.error(
            request,
            'Debes seleccionar un método de pago válido.'
        )
        return redirect('checkout_page')

    # Validar los campos simulados de tarjeta
    if metodo_pago in {'tarjeta_credito', 'tarjeta_debito'}:
        numero_tarjeta = re.sub(
            r'\D',
            '',
            request.POST.get('numero_tarjeta', '')
        )

        nombre_titular = (
            request.POST
            .get('nombre_titular', '')
            .strip()
        )

        fecha_vencimiento_mes = (
            request.POST
            .get('fecha_vencimiento_mes', '')
            .strip()
        )

        fecha_vencimiento_anio = (
            request.POST
            .get('fecha_vencimiento_anio', '')
            .strip()
        )

        cvv = (
            request.POST
            .get('cvv', '')
            .strip()
        )

        # Número de tarjeta: exactamente 16 dígitos
        if not re.fullmatch(r'\d{16}', numero_tarjeta):
            messages.error(
                request,
                'El número de tarjeta debe contener exactamente 16 dígitos.'
            )
            return redirect('checkout_page')

        # Titular: mínimo 3 caracteres y dos palabras
        palabras_titular = [
            palabra
            for palabra in re.split(r'\s+', nombre_titular)
            if palabra
        ]

        nombre_valido = re.fullmatch(
            r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+",
            nombre_titular
        )

        if (
                len(nombre_titular) < 3 or
                len(palabras_titular) < 2 or
                not nombre_valido
        ):
            messages.error(
                request,
                'El titular debe contener al menos nombre y apellido.'
            )
            return redirect('checkout_page')

        # CVV: exactamente 3 dígitos
        if not re.fullmatch(r'\d{3}', cvv):
            messages.error(
                request,
                'El CVV debe contener exactamente 3 números.'
            )
            return redirect('checkout_page')

        # Fecha de vencimiento
        try:
            mes_vencimiento = int(
                fecha_vencimiento_mes
            )

            anio_vencimiento = int(
                fecha_vencimiento_anio
            )

        except (TypeError, ValueError):
            messages.error(
                request,
                'Debes seleccionar una fecha de vencimiento válida.'
            )
            return redirect('checkout_page')

        fecha_actual = timezone.localdate()

        if mes_vencimiento < 1 or mes_vencimiento > 12:
            messages.error(
                request,
                'El mes de vencimiento no es válido.'
            )
            return redirect('checkout_page')

        if (
                anio_vencimiento < fecha_actual.year or
                anio_vencimiento > fecha_actual.year + 15
        ):
            messages.error(
                request,
                'El año de vencimiento no es válido.'
            )
            return redirect('checkout_page')

        if (
                anio_vencimiento == fecha_actual.year and
                mes_vencimiento < fecha_actual.month
        ):
            messages.error(
                request,
                'La tarjeta ya se encuentra vencida.'
            )
            return redirect('checkout_page')

    # Validar los campos simulados de PayPal
    elif metodo_pago == 'paypal':
        paypal_correo = request.POST.get('paypal_correo', '').strip()
        paypal_password = request.POST.get('paypal_password', '').strip()

        if not paypal_correo or not paypal_password:
            messages.error(
                request,
                'Debes completar el correo y la contraseña de PayPal.'
            )
            return redirect('checkout_page')

    detalles_del_carrito = cart.detallecarrito_set.select_related(
        'producto'
    ).all()

    # Verificar el stock antes de crear el pedido
    for item in detalles_del_carrito:
        producto = item.producto
        cantidad_pedida = item.cantidad

        if producto.stock < cantidad_pedida:
            messages.error(
                request,
                f"No hay suficiente stock para '{producto.nombre}'. "
                f"Cantidad disponible: {producto.stock}."
            )
            return redirect('checkout_page')

    domicilio = get_object_or_404_mongo(
        Domicilio,
        pk=domicilio_id,
        usuario=request.user
    )

    total_price = detalles_del_carrito.aggregate(
        total=Sum('subtotal')
    )['total'] or 0

    fecha_envio = timezone.now()
    fecha_llegada = fecha_envio + timedelta(days=7)

    envio = Envio.objects.create(
        domicilio=domicilio,
        fecha_envio=fecha_envio,
        fecha_llegada=fecha_llegada
    )

    pedido = Pedido.objects.create(
        usuario=request.user,
        envio=envio,
        carrito=cart,
        fecha=timezone.now(),
        subtotal=total_price,
        total_pagar=total_price
    )

    for item in detalles_del_carrito:
        DetallesPedido.objects.create(
            pedido=pedido,
            producto=item.producto,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario
        )

        item.producto.stock -= item.cantidad
        item.producto.save()

    Pago.objects.create(
        pedido=pedido,
        metodo_pago=metodo_pago,
        monto_pagar=total_price,
        estado='aprobado',
        fecha_pago=timezone.now()
    )

    cart.estado = 'convertido'
    cart.save()

    return redirect(
        'order_confirmation',
        order_id=str(pedido.id)
    )


@login_required
def order_confirmation(request, order_id):
    pedido = get_object_or_404_mongo(Pedido, pk=order_id, usuario=request.user)
    context = {
        'pedido': pedido
    }
    return render(request, 'order_confirmation.html', context)

# --- FIN: LÓGICA COMPLETA DE CHECKOUT CARRITO ---

# --- INICIO: VISTAS PARA FAVORITOS ---

@login_required
def toggle_favorite(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404_mongo(Producto, pk=producto_id)

        favorito, created = Favorito.objects.get_or_create(usuario=request.user, producto=producto)

        if not created:
            favorito.delete()
            is_favorited = False
        else:
            is_favorited = True

        return JsonResponse({'status': 'ok', 'is_favorited': is_favorited})

    return JsonResponse({'status': 'error'}, status=400)


@login_required
def favoritos_list(request):
    favoritos_qs = Favorito.objects.filter(usuario=request.user).values_list('producto_id', flat=True)

    productos_favoritos = Producto.objects.select_related(
        'marca', 'imgproducto', 'categoria'
    ).filter(pk__in=favoritos_qs)

    favoritos_ids = list(favoritos_qs)

    context = {
        'productos_favoritos': productos_favoritos,
        'favoritos_ids': favoritos_ids
    }
    return render(request, 'favoritos.html', context)

# --- FIN: VISTAS PARA FAVORITOS ---

# --- INICIO: LÓGICA COMPLETA DE MIS DEVOLUCIONES ADMIN ---

@staff_member_required
def gestionar_devoluciones(request):
    if request.method == 'POST':
        devolucion_id = request.POST.get('devolucion_id')
        nuevo_estado = request.POST.get('nuevo_estado')

        if devolucion_id and nuevo_estado in ['aceptada', 'rechazada']:
            devolucion = get_object_or_404_mongo(Devolucion, pk=devolucion_id)
            devolucion.estado = nuevo_estado
            devolucion.save()
            return redirect('gestionar_devoluciones')

    lista_devoluciones = Devolucion.objects.select_related('pedido__usuario').all().order_by('-fecha_devolucion')

    context = {
        'devoluciones': lista_devoluciones
    }
    return render(request, 'admin/gestionar_devoluciones.html', context)

# --- FIN: LÓGICA COMPLETA DE MIS DEVOLUCIONES ADMIN ---

# --- INICIO: LÓGICA COMPLETA DE MIS COMPRAS ADMIN ---

@staff_member_required
def gestionar_compras(request):
    pedidos = Pedido.objects.select_related(
        'usuario',
        'envio__domicilio'
    ).all().order_by('-fecha')

    compras = []

    for pedido in pedidos:
        detalles = DetallesPedido.objects.filter(
            pedido=pedido
        ).select_related('producto')

        pago = Pago.objects.filter(
            pedido=pedido
        ).first()

        compras.append({
            'id': pedido.id,
            'usuario': pedido.usuario,
            'detalles': detalles,
            'total': pedido.total_pagar,
            'domicilio': pedido.envio.domicilio if pedido.envio else None,
            'metodo_pago': pago.get_metodo_pago_display() if pago else 'No registrado',
            'fecha': pedido.fecha,
        })

    context = {
        'compras': compras
    }

    return render(request, 'admin/compras.html', context)

# --- FIN: LÓGICA COMPLETA DE MIS COMPRAS ADMIN ---

# --- INICIO: LÓGICA COMPLETA PARA CHATBOT ---

INSTRUCCIONES_DEL_SISTEMA = """
Eres ChronoBot, un asistente de ventas experto y amigable de la tienda de relojes de lujo ChronosLux.

Tu misión es responder las preguntas del cliente basándote EXCLUSIVAMENTE en la información de la base de datos que te proporciono a continuación.
NO inventes información. Si el cliente pregunta por algo que no está en la lista, infórmale amablemente que no lo manejas.

Sé conciso y servicial.

Si preguntan sobre devoluciones, los clientes tendrán un plazo máximo de 3 meses para hacer la devolución de un pedido.
Si preguntan cómo comprar, puedes decirles que visiten el apartado de catálogo normal o el de exclusivos para ver la variedad de relojes disponibles.
Los métodos de pago que manejamos son PayPal, tarjeta de crédito y tarjeta de débito.
Los envíos son gratis.

Formatea tus respuestas usando Markdown.
Para listas de productos, usa viñetas (*) y resalta los nombres de los relojes en negrita, por ejemplo: **Nombre del Reloj**.
"""


client_groq = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


def construir_info_bdd():
    productos_en_bdd = Producto.objects.filter(
        stock__gt=0,
        fecha_borrado__isnull=True
    )

    info_bdd_texto = "--- INFORMACIÓN DE LA BASE DE DATOS (Inventario Actual) ---\n"

    if productos_en_bdd:
        for producto in productos_en_bdd:
            info_bdd_texto += (
                f"* **{producto.marca.nombre} {producto.nombre}**: "
                f"Precio: ${producto.precio:,.2f} MXN. "
                f"Material: {producto.categoria.material}. "
                f"Género: {producto.categoria.genero}. "
                f"Stock: {producto.stock}.\n"
            )
    else:
        info_bdd_texto += "Actualmente no tenemos productos disponibles en la tienda.\n"

    info_bdd_texto += "--------------------------------------------------------\n"

    return info_bdd_texto


def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse(
            {'error': 'Esta ruta solo acepta solicitudes POST.'},
            status=405
        )

    if not settings.GROQ_API_KEY:
        return JsonResponse(
            {'error': 'No está configurada la clave GROQ_API_KEY.'},
            status=500
        )

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse(
                {'error': 'No se recibió ningún mensaje.'},
                status=400
            )

        info_bdd_texto = construir_info_bdd()

        prompt_final = f"""
{info_bdd_texto}

PREGUNTA DEL CLIENTE:
"{user_message}"
"""

        respuesta_stream = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": INSTRUCCIONES_DEL_SISTEMA
                },
                {
                    "role": "user",
                    "content": prompt_final
                }
            ],
            temperature=0.4,
            max_tokens=700,
            stream=True
        )

        def stream_generator():
            for chunk in respuesta_stream:
                contenido = chunk.choices[0].delta.content
                if contenido:
                    yield contenido

        return StreamingHttpResponse(
            stream_generator(),
            content_type='text/plain; charset=utf-8'
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'El cuerpo de la solicitud no es un JSON válido.'},
            status=400
        )

    except RateLimitError as e:
        print(f"Rate limit de Groq excedido: {e}")
        return JsonResponse(
            {'error': 'ChronoBot recibió demasiadas preguntas en poco tiempo. Intenta de nuevo en unos segundos.'},
            status=429
        )

    except APIError as e:
        print(f"Error de API Groq: {e}")
        return JsonResponse(
            {'error': 'El servicio de inteligencia artificial no respondió correctamente.'},
            status=502
        )

    except Exception as e:
        print(f"Error en la vista del chatbot: {e}")
        return JsonResponse(
            {'error': 'Ocurrió un error interno en el servidor.'},
            status=500
        )

# --- FIN: LÓGICA COMPLETA PARA CHATBOT ---
