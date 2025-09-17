from django.db import models
from django.conf import settings
from django.utils import timezone


class Usuario(models.Model):
    nombre = models.CharField(max_length=40)
    apellido = models.CharField(max_length=55)
    correo = models.EmailField(unique=True, max_length=120)
    password = models.CharField(max_length=255)
    rol = models.CharField(max_length=15, default='cliente')

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Marca(models.Model):
    nombre = models.CharField(max_length=60)

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    genero = models.CharField(max_length=60)
    material = models.CharField(max_length=60)

    def __str__(self):
        return f"{self.genero} - {self.material}"


class Proveedor(models.Model):
    nombre_empresa = models.CharField(max_length=50)
    producto_suministrado = models.TextField(blank=True, null=True)
    cantidad_producto = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.nombre_empresa


class Producto(models.Model):
    nombre = models.CharField(max_length=60)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=140, blank=True, null=True)
    stock = models.IntegerField(default=0)
    fecha_borrado = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(blank=True, null=True)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class ImgProducto(models.Model):
    url = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE)

    def __str__(self):
        return f"Imagen de {self.producto.nombre}"


class Carrito(models.Model):
    ESTADOS = (
        ('activo', 'Activo'),
        ('expirado', 'Expirado'),
        ('convertido', 'Convertido'),
    )
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    fecha_expiracion = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return f"Carrito {self.id} de {self.usuario}"


class DetalleCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


class Domicilio(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    calle = models.CharField(max_length=150)
    num_ext = models.CharField(max_length=20)
    num_int = models.CharField(max_length=20, blank=True, null=True)
    colonia = models.CharField(max_length=120)
    estado = models.CharField(max_length=120)
    cp = models.CharField(max_length=10)
    pais = models.CharField(max_length=80)

    def __str__(self):
        return f"{self.calle}, {self.colonia}, {self.estado}"


class Envio(models.Model):
    fecha_envio = models.DateTimeField(blank=True, null=True)
    fecha_llegada = models.DateTimeField(blank=True, null=True)
    domicilio = models.ForeignKey(Domicilio, on_delete=models.CASCADE)

    def __str__(self):
        return f"Envio {self.id}"


class Pedido(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    carrito = models.ForeignKey(Carrito, on_delete=models.SET_NULL, blank=True, null=True)
    envio = models.OneToOneField(Envio, on_delete=models.CASCADE, blank=True, null=True)
    fecha = models.DateTimeField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    total_pagar = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Pedido {self.id} - {self.usuario}"


class DetallesPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


class Pago(models.Model):
    METODOS = (
        ('tarjeta', 'Tarjeta'),
        ('paypal', 'PayPal'),
    )
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    )
    metodo_pago = models.CharField(max_length=20, choices=METODOS)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_pago = models.DateTimeField(blank=True, null=True)
    monto_pagar = models.DecimalField(max_digits=12, decimal_places=2)
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE)

    def __str__(self):
        return f"Pago {self.id} - {self.metodo_pago}"


class Resena(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    calificacion = models.IntegerField()
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Reseña de {self.usuario} sobre {self.producto}"


class Devolucion(models.Model):
    ESTADOS = (
        ('solicitada', 'Solicitada'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    )
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    fecha_devolucion = models.DateTimeField(blank=True, null=True)
    url_img_prod_devuelto = models.CharField(max_length=255, blank=True, null=True)
    descripcion_devolucion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='solicitada')

    def __str__(self):
        return f"Devolución {self.id} - {self.pedido}"


class Favorito(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'producto')

    def __str__(self):
        return f"{self.usuario} ❤ {self.producto}"

