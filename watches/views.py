import os
import uuid
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Producto, Categoria, Resena, ImgProducto, Marca, Domicilio, DetallesPedido, Pedido, Envio, Pago, Favorito, Carrito, DetalleCarrito, Devolucion
from django.http import JsonResponse, StreamingHttpResponse
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
import google.generativeai as genai


# --- INICIO: LÓGICA COMPLETA DE LA VISTA DE HOME ---

def home(request):
    context = home_page_context(request)
    return render(request, 'home.html', context)

# --- FIN: LÓGICA COMPLETA DE LA VISTA DE HOME ---

# --- INICIO: LÓGICA COMPLETA DE VISTA Y FILTROS NORMALES ---

def catalog(request):
    items = Producto.objects.select_related('categoria', 'marca', 'imgproducto').filter(es_exclusivo=False)

    # Barra de busqueda
    query = request.GET.get('q')
    if query:
        items = items.filter(
            Q(nombre__icontains=query) |
            Q(marca__nombre__icontains=query) |
            Q(descripcion1__icontains=query) |
            Q(descripcion2__icontains=query) |
            Q(descripcion3__icontains=query)
        )

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
        favoritos_ids = list(Favorito.objects.filter(usuario=request.user).values_list('producto_id', flat=True))

    tipos_disponibles = Categoria.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
    generos_disponibles = Categoria.objects.values_list('genero', flat=True).distinct().order_by('genero')
    marcas_disponibles = Marca.objects.all().order_by('nombre')

    # Paginación
    page_number = request.GET.get('page') or 1
    paginator = Paginator(items, 12)
    page_obj = paginator.get_page(page_number)

    return render(request, 'catalog.html', {
        'page_obj': page_obj,
        'catalog_watches': page_obj.object_list,
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
    producto = get_object_or_404(
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
    if not created and cart.fecha_expiracion < timezone.now():
        cart.estado = 'expirado'
        cart.save()
        # Y crea uno nuevo.
        cart = Carrito.objects.create(
            usuario=request.user,
            fecha_creacion=timezone.now(),
            fecha_expiracion=timezone.now() + timedelta(minutes=60)
        )
    return cart


def add_to_cart(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
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
                    'id': item.producto.id,
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
        action = json.loads(request.body).get('action')

        if request.user.is_authenticated:
            cart = _get_user_cart(request)
            detalle = get_object_or_404(DetalleCarrito, carrito=cart, producto_id=producto_id)
            if action == 'increase':
                detalle.cantidad += 1
            elif action == 'decrease':
                detalle.cantidad -= 1

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
    producto = get_object_or_404(Producto, pk=producto_id)

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
    producto = get_object_or_404(Producto, pk=producto_id)

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
        favoritos_ids = list(Favorito.objects.filter(usuario=request.user).values_list('producto_id', flat=True))

    tipos_disponibles = Categoria.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
    generos_disponibles = Categoria.objects.values_list('genero', flat=True).distinct().order_by('genero')
    marcas_disponibles = Marca.objects.all().order_by('nombre')

    paginator = Paginator(items, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'productos_exclusivos': page_obj,
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
                'id': item.producto.id,
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
    if request.method == 'POST':
        cart = _get_user_cart(request)
        domicilio_id = request.POST.get('domicilio_seleccionado')
        metodo_pago = request.POST.get('metodo_pago')

        if not cart or not cart.detallecarrito_set.all() or not domicilio_id or not metodo_pago:
            messages.error(request, 'Hubo un error con tu pedido. Por favor, intenta de nuevo.')
            return redirect('checkout_page')

        #  --- VERIFICACIÓN DE STOCK ---
        detalles_del_carrito = cart.detallecarrito_set.all()
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

        domicilio = get_object_or_404(Domicilio, pk=domicilio_id, usuario=request.user)
        total_price = detalles_del_carrito.aggregate(total=Sum('subtotal'))['total'] or 0

        # Crear el Envío
        fecha_envio = timezone.now()
        fecha_llegada = fecha_envio + timedelta(days=7)
        envio = Envio.objects.create(
            domicilio=domicilio,
            fecha_envio=fecha_envio,
            fecha_llegada=fecha_llegada
        )

        # Crear el Pedido
        pedido = Pedido.objects.create(
            usuario=request.user,
            envio=envio,
            carrito=cart,
            fecha=timezone.now(),
            subtotal=total_price,
            total_pagar=total_price
        )

        # Crear los Detalles del Pedido y DESCONTAR STOCK
        for item in detalles_del_carrito:
            DetallesPedido.objects.create(
                pedido=pedido,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario
            )
            item.producto.stock -= item.cantidad
            item.producto.save()

        # Crear el Pago
        Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo_pago,
            monto_pagar=total_price,
            estado='aprobado'
        )

        # Actualizamos el estado del carrito a 'convertido'
        cart.estado = 'convertido'
        cart.save()

        # Redirigir a confirmación
        return redirect('order_confirmation', order_id=pedido.id)

    return redirect('home')

@login_required
def order_confirmation(request, order_id):
    pedido = get_object_or_404(Pedido, pk=order_id, usuario=request.user)
    context = {
        'pedido': pedido
    }
    return render(request, 'order_confirmation.html', context)

# --- FIN: LÓGICA COMPLETA DE CHECKOUT CARRITO ---

# --- INICIO: VISTAS PARA FAVORITOS ---

@login_required
def toggle_favorite(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, pk=producto_id)

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
    favoritos_ids = Favorito.objects.filter(usuario=request.user).values_list('producto_id', flat=True)
    productos_favoritos = Producto.objects.select_related('marca', 'imgproducto', 'categoria').filter(
        pk__in=favoritos_ids)

    context = {
        'productos_favoritos': productos_favoritos,
        'favoritos_ids': list(favoritos_ids)
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
            devolucion = get_object_or_404(Devolucion, pk=devolucion_id)
            devolucion.estado = nuevo_estado
            devolucion.save()
            return redirect('gestionar_devoluciones')

    lista_devoluciones = Devolucion.objects.select_related('pedido__usuario').all().order_by('-fecha_devolucion')

    context = {
        'devoluciones': lista_devoluciones
    }
    return render(request, 'admin/gestionar_devoluciones.html', context)

# --- FIN: LÓGICA COMPLETA DE MIS DEVOLUCIONES ADMIN ---

# --- INICIO: LÓGICA COMPLETA PARA CHATBOT ---

try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except AttributeError:
    print("ERROR: La clave GEMINI_API_KEY no se encontró en settings.py")
    genai.configure(api_key="CLAVE_NO_CONFIGURADA")

INSTRUCCIONES_DEL_SISTEMA = """
Eres ChronoBot, un asistente de ventas experto y amigable de la tienda de relojes de lujo ChronosLux.
Tu misión es responder las preguntas del cliente basándote EXCLUSIVAMENTE en la información de la base de datos que te proporciono a continuación.
NO inventes información. Si el cliente pregunta por algo que no está en la lista, infórmale amablemente que no lo manejas.
Sé conciso y servicial.
Si preguntan sobre devoluciones, los clientes tendrán un plazo maximo de 3 meses para hacer la devolución de un pedido.
Si preguntan para hacer compras puedes decirle que visten el apartado de catalogo ya sea el normal o el de exclusivos para ver la variedad de relojes que tenemos,
los metodos de pago que manejamos son 3 paypal, tarjeta de credito y debito, los envios son gratis.
**Formatea tus respuestas usando Markdown. Para listas de productos, usa viñetas (*) y resalta los nombres de los relojes en negrita (**Nombre del Reloj**).**
"""

modelo_gemini = genai.GenerativeModel(
    model_name="models/gemini-flash-latest",
    system_instruction=INSTRUCCIONES_DEL_SISTEMA
)

def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Esta ruta solo acepta solicitudes POST.'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'No se recibió ningún mensaje.'}, status=400)


        productos_en_bdd = Producto.objects.select_related('marca', 'categoria').filter(stock__gt=0,
                                                                                        fecha_borrado__isnull=True)

        info_bdd_texto = "--- INFORMACIÓN DE LA BASE DE DATOS (Inventario Actual) ---\n"
        if productos_en_bdd:
            for producto in productos_en_bdd:
                info_bdd_texto += (
                    f"* **{producto.marca.nombre} {producto.nombre}**: "
                    f"Precio: ${producto.precio:,.2f} MXN. "
                    f"Material: {producto.categoria.material}. "
                    f"Género: {producto.categoria.genero}.\n"
                )
        else:
            info_bdd_texto += "Actualmente no tenemos productos disponibles en la tienda.\n"

        info_bdd_texto += "--------------------------------------------------------\n"

        prompt_final = f"{info_bdd_texto}\nPREGUNTA DEL CLIENTE: \"{user_message}\""

        chat = modelo_gemini.start_chat(history=[])
        respuesta_stream = chat.send_message(prompt_final, stream=True)

        def stream_generator():
            for chunk in respuesta_stream:
                yield chunk.text

        return StreamingHttpResponse(stream_generator(), content_type='text/plain; charset=utf-8')

    except json.JSONDecodeError:
        return JsonResponse({'error': 'El cuerpo de la solicitud no es un JSON válido.'}, status=400)
    except Exception as e:
        print(f"Error en la vista del chatbot: {e}")
        return JsonResponse({'error': 'Ocurrió un error interno en el servidor.'}, status=500)

# --- FIN: LÓGICA COMPLETA PARA CHATBOT ---