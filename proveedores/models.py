from django.db import models
from django.conf import settings
from watches.models import Producto

class Proveedor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombre_empresa = models.CharField(max_length=200)
    telefono_contacto = models.CharField(max_length=50, blank=True)
    direccion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_empresa

class Compra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    total_compra = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Compra a {self.proveedor.nombre_empresa} el {self.fecha_compra.strftime('%d-%m-%Y')}"

class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en {self.compra}"

    def subtotal(self):
        return self.cantidad * self.costo_unitario
