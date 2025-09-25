from .models import Carrito, DetalleCarrito
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