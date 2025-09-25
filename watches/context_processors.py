def cart_context(request):
    cart = request.session.get('cart', {})
    total_items = sum(item.get('quantity', 0) for item in cart.values())
    return {
        'cart_total_items': total_items
    }