from django.contrib import admin
from .models import Proveedor, Compra, DetalleCompra


# Registramos los tres modelos para que aparezcan en el panel de admin
admin.site.register(Proveedor)
admin.site.register(Compra)
admin.site.register(DetalleCompra)