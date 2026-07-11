from .models import Carrito, DetalleCarrito,  Producto, Marca, Favorito
from django.db.models import Sum


def cart_context(request):
    total_items = 0
    if request.user.is_authenticated:
        carrito_activo = Carrito.objects.filter(usuario=request.user, estado='activo').first()
        if carrito_activo:
            resultado = DetalleCarrito.objects.filter(carrito=carrito_activo).aggregate(total=Sum('cantidad'))
            total_items = resultado['total'] or 0
    else:
        cart_session = request.session.get('cart', {})
        total_items = sum(item.get('quantity', 0) for item in cart_session.values())

    return {
        'cart_total_items': total_items
    }

# --- INICIO: LÓGICA COMPLETA DE LA VISTA DE HOME ---

def home_page_context(request):
    # --- SECCIÓN DE RELOJES DESTACADOS ---
    relojes_destacados = Producto.objects.select_related(
        'marca', 'imgproducto', 'categoria'
    ).filter(
        fecha_borrado__isnull=True,
        es_exclusivo=False
    )[:3]

    # --- SECCIÓN DE CATÁLOGO EN HOME ---
    relojes_catalogo_home = Producto.objects.select_related(
        'marca', 'imgproducto', 'categoria'
    ).filter(
        fecha_borrado__isnull=True,
        es_exclusivo=False
    )[:8]

    marcas = Marca.objects.all().order_by('nombre')

    # --- SECCIÓN DEL RELOJ EXCLUSIVO ---
    reloj_exclusivo_destacado = Producto.objects.select_related(
        'marca', 'imgproducto', 'categoria'
    ).filter(
        fecha_borrado__isnull=True,
        es_exclusivo=True,
        nombre__iexact="Royal Oak",
        marca__nombre__iexact="Audemars Piguet"
    ).first()

    # --- LÓGICA PARA OBTENER FAVORITOS ---
    favoritos_ids = []

    if request.user.is_authenticated:
        favoritos_ids = list(
            Favorito.objects.filter(
                usuario=request.user
            ).values_list('producto_id', flat=True)
        )

    return {
        'featured_watches': relojes_destacados,
        'catalog_watches': relojes_catalogo_home,
        'marcas': marcas,
        'exclusive_watch': reloj_exclusivo_destacado,
        'favoritos_ids': favoritos_ids,
    }

# --- FIN: LÓGICA COMPLETA DE LA VISTA DE HOME ---
