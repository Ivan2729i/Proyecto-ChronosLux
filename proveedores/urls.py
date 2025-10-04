from django.urls import path
from . import views

urlpatterns = [
    path('', views.portal_proveedor, name='portal_proveedor'),
    path('crear-compra/', views.crear_compra, name='crear_compra'),
    path('historial/', views.historial_compras, name='historial_compras'),
]
