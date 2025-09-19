from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Producto, Categoria, Resena
from django.http import JsonResponse
import json

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

def catalog(request):
    # Consultar los relojes de la base de datos
    items = Producto.objects.select_related('categoria', 'marca', 'imgproducto').all()

    # Filtros
    t = (request.GET.get('type') or '').lower()
    price = (request.GET.get('price') or '').lower()
    gender = (request.GET.get('gender') or '').lower()

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

    # Aplicar filtros
    items = [x for x in items if match_type(x) and match_price(x) and match_gender(x)]

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

    # Paginación
    page_number = request.GET.get('page') or 1
    paginator = Paginator(items, 12)
    page_obj = paginator.get_page(page_number)

    return render(request, 'catalog.html', {
        'page_obj': page_obj,
        'catalog_watches': page_obj.object_list,
        'querystring': request.GET.urlencode(),
        'current': {
            'type': t or 'all',
            'price': price or 'all',
            'gender': gender or 'all',
            'sort': sort or 'featured',
        },
        'tipos': tipos_disponibles,
        'generos': generos_disponibles,
    })

def product_detail(request, producto_id):
    # Usamos get_object_or_404 para obtener el producto o mostrar un error 404 si no existe
    producto = get_object_or_404(
        Producto.objects.select_related('categoria', 'marca', 'imgproducto'),
        pk=producto_id
    )

    # Obtenemos todas las reseñas asociadas a este producto
    reseñas = Resena.objects.filter(producto=producto).order_by('-fecha')

    context = {
        'producto': producto,
        'reseñas': reseñas,
    }
    return render(request, 'catalog/product_detail.html', context)


# --- VISTAS PARA LA API DEL CARRITO ---

def add_to_cart(request, producto_id):
    # Agrega un producto al carrito en la sesión. Si ya existe, incrementa la cantidad.
    # Obtenemos el producto desde la base de datos para asegurar que existe y tener el precio real.
    producto = get_object_or_404(Producto, pk=producto_id)

    # Obtenemos el carrito de la sesión. Si no existe, es un diccionario vacío.
    cart = request.session.get('cart', {})
    pid_str = str(producto.id)

    if pid_str in cart:
        # Si el reloj ya está en el carrito, solo aumentamos su cantidad.
        cart[pid_str]['quantity'] += 1
    else:
        # Si es la primera vez que se agrega, guardamos sus datos.
        cart[pid_str] = {
            'quantity': 1,
            'price': str(producto.precio),  # Guardamos el precio como string
            'name': producto.nombre,
            'image_url': producto.imgproducto.url,
            'brand': producto.marca.nombre
        }

    # Guardamos el carrito modificado de vuelta en la sesión.
    request.session['cart'] = cart

    # Calculamos el total de items para actualizar el ícono del carrito en el frontend.
    total_items = sum(item['quantity'] for item in cart.values())

    return JsonResponse({'status': 'ok', 'total_items': total_items})


def remove_from_cart(request, producto_id):
    """
    Elimina un producto completo del carrito.
    """
    cart = request.session.get('cart', {})
    pid_str = str(producto_id)

    if pid_str in cart:
        # Si el producto existe en el carrito, lo eliminamos.
        del cart[pid_str]

    # Guardamos el carrito modificado.
    request.session['cart'] = cart
    total_items = sum(item['quantity'] for item in cart.values())

    return JsonResponse({'status': 'ok', 'total_items': total_items})


def update_cart_quantity(request, producto_id):
    """
    Actualiza la cantidad de un producto (incrementa o decrementa).
    Si la cantidad llega a cero, elimina el producto.
    """
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        pid_str = str(producto_id)

        if pid_str in cart:
            # Leemos la acción ('increase' o 'decrease') del cuerpo de la petición.
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'increase':
                cart[pid_str]['quantity'] += 1
            elif action == 'decrease':
                cart[pid_str]['quantity'] -= 1
                # Si la cantidad es 0 o menos, eliminamos el item del carrito.
                if cart[pid_str]['quantity'] <= 0:
                    del cart[pid_str]

            # Guardamos el carrito modificado.
            request.session['cart'] = cart
            total_items = sum(item['quantity'] for item in cart.values())

            return JsonResponse({'status': 'ok', 'total_items': total_items})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def get_cart_data(request):
    """
    Una vista de API que devuelve los datos del carrito en la sesión como JSON.
    """
    cart = request.session.get('cart', {})
    items = []
    total_price = 0
    total_items = 0

    for pid, item_data in cart.items():
        subtotal = item_data['quantity'] * float(item_data['price'])
        items.append({
            'id': pid,
            'name': item_data['name'],
            'brand': item_data.get('brand', ''), # Usamos .get para seguridad
            'quantity': item_data['quantity'],
            'price': float(item_data['price']),
            'image_url': item_data['image_url'],
            'subtotal': subtotal
        })
        total_price += subtotal
        total_items += item_data['quantity']

    return JsonResponse({
        'cart_items': items,
        'total_price': total_price,
        'total_items': total_items,
    })
