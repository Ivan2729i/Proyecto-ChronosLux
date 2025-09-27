from .models import Carrito, DetalleCarrito,  Producto, Marca, Favorito
from django.db.models import Sum


def cart_context(request):
    total_items = 0
    if request.user.is_authenticated:
        # Lógica para usuarios logueados
        carrito_activo = Carrito.objects.filter(usuario=request.user, estado='activo').first()
        if carrito_activo:
            resultado = DetalleCarrito.objects.filter(carrito=carrito_activo).aggregate(total=Sum('cantidad'))
            total_items = resultado['total'] or 0
    else:
        # Lógica para usuarios anónimos (sesión)
        cart_session = request.session.get('cart', {})
        total_items = sum(item.get('quantity', 0) for item in cart_session.values())

    return {
        'cart_total_items': total_items
    }

# --- INICIO: LÓGICA COMPLETA DE LA VISTA DE HOME ---
def home_page_context(request):
    # --- SECCIÓN DE RELOJES DESTACADOS ---
    ids_destacados = [9, 12, 16]
    relojes_destacados = Producto.objects.select_related('marca', 'imgproducto', 'categoria').filter(
        id__in=ids_destacados)

    # --- SECCIÓN DE CATÁLOGO EN HOME ---
    ids_catalogo_home = [10, 13, 15, 17, ]
    relojes_catalogo_home = Producto.objects.select_related('marca', 'imgproducto', 'categoria').filter(
        id__in=ids_catalogo_home)
    marcas = Marca.objects.all().order_by('nombre')

    # --- SECCIÓN DEL RELOJ EXCLUSIVO ---
    id_exclusivo = 21
    reloj_exclusivo_destacado = Producto.objects.select_related(
        'marca', 'imgproducto', 'categoria'
    ).filter(id=id_exclusivo, es_exclusivo=True).first()

    # --- LÓGICA PARA OBTENER FAVORITOS ---
    favoritos_ids = []
    if request.user.is_authenticated:
        favoritos_ids = list(Favorito.objects.filter(usuario=request.user).values_list('producto_id', flat=True))

    # Devuelve el diccionario de contexto completo
    return {
        'featured_watches': relojes_destacados,
        'catalog_watches': relojes_catalogo_home,
        'marcas': marcas,
        'exclusive_watch': reloj_exclusivo_destacado,
        'favoritos_ids': favoritos_ids,
    }



# --- FIN: LÓGICA COMPLETA DE LA VISTA DE HOME ---