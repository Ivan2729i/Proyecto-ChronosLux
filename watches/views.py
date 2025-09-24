import os
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Producto, Categoria, Resena, ImgProducto, Marca, Domicilio, DetallesPedido, Pedido, Envio, Pago
from django.http import JsonResponse
import json
from .forms import ProductoForm
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta


def build_home_context():
    featured_watches = [
        {
            'id': 1,
            'name': 'Submariner Date',
            'brand': 'Rolex',
            "type": "Deportivo",
            'price': 12500,
            'image': '/static/img/rolex-submariner.jpg',
            'rating': 4.9,
            'features': ['Resistente al agua 300m', 'Movimiento automático', 'Cristal de zafiro']
        },
        {
            'id': 2,
            'name': 'Speedmaster Professional',
            'brand': 'Omega',
            "type": "Casual",
            'price': 6800,
            'image': '/placeholder.svg?height=400&width=400',
            'rating': 4.9,
            'features': ['Cronógrafo manual', 'Certificado por la NASA', 'Resistente a campos magnéticos']
        },
        {
            'id': 3,
            'name': 'Royal Oak',
            'brand': 'Audemars Piguet',
            'price': 28000,
            'image': '/placeholder.svg?height=400&width=400',
            'rating': 5.0,
            'features': ['Caja octagonal icónica', 'Movimiento ultra-delgado', 'Acabado artesanal']
        }
    ]

    catalog_watches = [
        {
            'id': 4,
            'name': 'Datejust 36',
            'brand': 'Rolex',
            'price': 8900,
            'image': '/static/img/placeholder.jpg',
            'rating': 4.8,
            'features': ['Acero y oro', 'Fecha instantánea', 'Movimiento perpetuo']
        },
        {
            'id': 5,
            'name': 'Seamaster Planet Ocean',
            'brand': 'Omega',
            'price': 5200,
            'image': '/placeholder.svg?height=300&width=300',
            'rating': 4.7,
            'features': ['Resistente al agua 600m', 'Bisel unidireccional', 'Co-Axial Master Chronometer']
        },
        {
            'id': 6,
            'name': 'Millenary',
            'brand': 'Audemars Piguet',
            'price': 22000,
            'image': '/placeholder.svg?height=300&width=300',
            'rating': 4.9,
            'features': ['Caja ovalada', 'Movimiento visible', 'Edición limitada']
        },
        {
            'id': 7,
            'name': 'GMT-Master II',
            'brand': 'Rolex',
            'price': 15200,
            'image': '/placeholder.svg?height=300&width=300',
            'rating': 5.0,
            'features': ['Doble zona horaria', 'Bisel Pepsi', 'Movimiento GMT']
        },
        {
            'id': 8,
            'name': 'De Ville Prestige',
            'brand': 'Omega',
            'price': 3800,
            'image': '/placeholder.svg?height=300&width=300',
            'rating': 4.6,
            'features': ['Diseño clásico', 'Movimiento Co-Axial', 'Caja delgada']
        },
        {
            'id': 1,
            'name': 'Submariner Date',
            'brand': 'Rolex',
            "type": "Deportivo",
            "gender": "Hombre",
            'price': 12500,
            'image': '/static/img/rolex-submariner.jpg',
            'rating': 4.9,
            'features': ['Resistente al agua 300m', 'Movimiento automático', 'Cristal de zafiro']
        },
    ]

    return {'featured_watches': featured_watches, 'catalog_watches': catalog_watches}

def home(request):
    return render(request, 'home.html', build_home_context())

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
    })

def product_detail(request, producto_id):
    producto = get_object_or_404(
        Producto.objects.select_related('categoria', 'marca', 'imgproducto'),
        pk=producto_id
    )
    reseñas = Resena.objects.filter(producto=producto).order_by('-fecha')

    if producto.es_exclusivo:
        template_name = 'catalog/exclusive_product_detail.html'
    else:
        template_name = 'catalog/product_detail.html'

    context = {
        'producto': producto,
        'reseñas': reseñas,
    }
    return render(request, template_name, context)

# --- FIN: LÓGICA COMPLETA DE VISTA Y FILTROS NORMALES ---

# --- INICIO: LÓGICA COMPLETA DEL CARRITO ---

def add_to_cart(request, producto_id):
    """ Agrega un producto al carrito en la sesión o incrementa su cantidad. """
    producto = get_object_or_404(Producto, pk=producto_id)
    cart = request.session.get('cart', {})
    pid_str = str(producto.id)

    if pid_str in cart:
        cart[pid_str]['quantity'] += 1
    else:
        cart[pid_str] = {
            'quantity': 1,
            'price': str(producto.precio),
            'name': producto.nombre,
            'image_url': producto.imgproducto.url.name,
            'brand': producto.marca.nombre
        }

    request.session['cart'] = cart
    total_items = sum(item['quantity'] for item in cart.values())
    return JsonResponse({'status': 'ok', 'total_items': total_items})


def remove_from_cart(request, producto_id):
    """ Elimina un producto completo del carrito. """
    cart = request.session.get('cart', {})
    pid_str = str(producto_id)

    if pid_str in cart:
        del cart[pid_str]

    request.session['cart'] = cart
    return JsonResponse({'status': 'ok'})


def update_cart_quantity(request, producto_id):
    """ Actualiza la cantidad de un producto (+/-). """
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        pid_str = str(producto_id)

        if pid_str in cart:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'increase':
                cart[pid_str]['quantity'] += 1
            elif action == 'decrease':
                cart[pid_str]['quantity'] -= 1
                if cart[pid_str]['quantity'] <= 0:
                    del cart[pid_str]

            request.session['cart'] = cart
            return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error'}, status=400)


def get_cart_data(request):
    """ Devuelve los datos completos del carrito para que JavaScript los pueda mostrar. """
    cart = request.session.get('cart', {})
    items_in_cart = []
    total_price = 0
    total_items = 0

    for pid, item in cart.items():
        subtotal = item['quantity'] * float(item['price'])
        items_in_cart.append({
            'id': pid,
            'name': item['name'],
            'brand': item.get('brand', ''),
            'quantity': item['quantity'],
            'price': float(item['price']),
            'image_url': item['image_url'],
            'subtotal': subtotal
        })
        total_price += subtotal
        total_items += item['quantity']

    return JsonResponse({
        'cart_items': items_in_cart,
        'total_price': total_price,
        'total_items': total_items,
    })

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
            producto.save()

            # --- Lógica para guardar la imagen ---
            uploaded_image = form.cleaned_data.get('imagen')
            if uploaded_image:
                extension = os.path.splitext(uploaded_image.name)[1]
                nombre_unico = f"{uuid.uuid4()}{extension}"
                uploaded_image.name = nombre_unico

                # Como el 'producto' ya está guardado, esta línea ahora funcionará
                ImgProducto.objects.create(producto=producto, url=uploaded_image)

            return redirect('admin_dashboard')
    else:
        form = ProductoForm()

    context = {'form': form}
    return render(request, 'admin/producto_form.html', context)


def editar_producto(request, producto_id):
    # Buscamos el producto que se va a editar, o mostramos un error 404 si no existe
    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        # Si el formulario se envía, lo procesamos con los datos nuevos y el producto existente
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            # (La lógica de la categoría y la imagen la moveremos aquí también)
            categoria_obj, created = Categoria.objects.get_or_create(
                genero=form.cleaned_data.get('genero'),
                material=form.cleaned_data.get('material'),
                tipo=form.cleaned_data.get('tipo')
            )

            edited_producto = form.save(commit=False)
            edited_producto.categoria = categoria_obj
            edited_producto.save()

            # Lógica para la imagen (si se sube una nueva)
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
        # 1. Verificamos si el producto tiene una imagen asociada para evitar errores.
        if hasattr(producto, 'imgproducto'):
            # 2. Borramos el archivo de imagen del disco.
            producto.imgproducto.url.delete(save=False)

        # 3. Borramos el producto (y el ImgProducto asociado) de la base de datos.
        producto.delete()

        return redirect('admin_dashboard')

    context = {
        'producto': producto
    }
    return render(request, 'admin/eliminar_producto.html', context)

# --- FIN: LÓGICA COMPLETA DE ADMIN ---

# --- INICIO: LÓGICA COMPLETA DE VISTA Y FILTROS EXCLUSIVE ---
def exclusivos_catalog(request):
    # 1. Obtenemos solo los productos marcados como exclusivos
    items = Producto.objects.select_related('marca', 'imgproducto', 'categoria').filter(es_exclusivo=True)

    # 2. Obtenemos los parámetros de filtro de la URL
    tipo_filtro = request.GET.get('type', '').lower()
    precio_filtro = request.GET.get('price', '').lower()
    genero_filtro = request.GET.get('gender', '').lower()
    sort_order = request.GET.get('sort', 'featured').lower()
    marca_filtro = request.GET.get('brand', '').lower()

    # 3. Aplicamos los filtros a la lista de productos
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

    # 4. Aplicamos el ordenamiento
    if sort_order == 'price_asc':
        items = items.order_by('precio')
    elif sort_order == 'price_desc':
        items = items.order_by('-precio')
    elif sort_order == 'name_asc':
        items = items.order_by('nombre')

    # 5. Obtenemos TODAS las opciones de filtros para poblar los menús
    tipos_disponibles = Categoria.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
    generos_disponibles = Categoria.objects.values_list('genero', flat=True).distinct().order_by('genero')
    marcas_disponibles = Marca.objects.all().order_by('nombre')

    # 6. Paginación
    paginator = Paginator(items, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # 7. Preparamos el contexto completo para la plantilla
    context = {
        'productos_exclusivos': page_obj,  # La plantilla itera sobre esto
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
    }

    return render(request, 'exclusivos_catalog.html', context)

# --- FIN: LÓGICA COMPLETA DE FILTROS EXCLUSIVE ---

# --- INICIO: LÓGICA COMPLETA DE CHECKOUT CARRITO ---

@login_required
def checkout_page(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    for pid, item_data in cart.items():
        subtotal = item_data['quantity'] * float(item_data['price'])
        cart_items.append({
            'id': pid,
            'name': item_data['name'],
            'brand': item_data.get('brand', ''),
            'quantity': item_data['quantity'],
            'price': float(item_data['price']),
            'image_url': item_data['image_url'],
            'subtotal': subtotal
        })
        total_price += subtotal

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
        cart = request.session.get('cart', {})
        domicilio_id = request.POST.get('domicilio_seleccionado')
        metodo_pago = request.POST.get('metodo_pago')

        if not cart or not domicilio_id or not metodo_pago:
            return redirect('checkout_page')

        domicilio = get_object_or_404(Domicilio, pk=domicilio_id, usuario=request.user)
        total_price = sum(item['quantity'] * float(item['price']) for item in cart.values())

        # 1. Crear el Envío
        fecha_envio = timezone.now()
        fecha_llegada = fecha_envio + timedelta(days=7)
        envio = Envio.objects.create(
            domicilio=domicilio,
            fecha_envio=fecha_envio,
            fecha_llegada=fecha_llegada
        )

        # 2. Crear el Pedido (CON LA CORRECCIÓN)
        pedido = Pedido.objects.create(
            usuario=request.user,
            envio=envio,
            fecha=timezone.now(),
            subtotal=total_price,  # ✅ LÍNEA AÑADIDA
            total_pagar=total_price
        )

        # 3. Crear los Detalles del Pedido
        for pid, item_data in cart.items():
            producto = get_object_or_404(Producto, pk=pid)
            DetallesPedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=item_data['quantity'],
                precio_unitario=float(item_data['price'])
            )

        # 4. Crear el Pago
        Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo_pago,
            monto_pagar=total_price,
            estado='aprobado'
        )

        # 5. Limpiar el carrito
        del request.session['cart']

        # 6. Redirigir a confirmación
        return redirect('order_confirmation', order_id=pedido.id)

    return redirect('home')


@login_required
def order_confirmation(request, order_id):
    pedido = get_object_or_404(Pedido, pk=order_id, usuario=request.user)
    context = {
        'pedido': pedido
    }
    return render(request, 'order_confirmation.html', context)