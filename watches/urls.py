from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', views.catalog, name='catalog'),
    path('producto/<int:producto_id>/', views.product_detail, name='product_detail'),

    path('carrito/agregar/<int:producto_id>/', views.add_to_cart, name='add_to_cart'),
    path('carrito/eliminar/<int:producto_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('carrito/actualizar/<int:producto_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('api/carrito/', views.get_cart_data, name='get_cart_data'),

    path('accounts/', include('accounts.urls')),
]
