import os
from decimal import Decimal

import pymysql
from django.core.management.base import BaseCommand
from django.utils import timezone
from dotenv import load_dotenv

from accounts.models import User
from watches.models import (
    Marca,
    Categoria,
    Producto,
    Domicilio,
    Carrito,
    DetalleCarrito,
    Envio,
    Pedido,
    DetallesPedido,
    Pago,
    Devolucion,
)


def make_aware_if_needed(value):
    if value is None:
        return None

    if timezone.is_naive(value):
        return timezone.make_aware(value)

    return value


def money(value):
    return Decimal(str(value or "0"))


class Command(BaseCommand):
    help = "Migra carritos, pedidos, envíos, pagos y devoluciones desde MySQL viejo a MongoDB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra conteos, no migra datos."
        )

    def handle(self, *args, **options):
        load_dotenv()

        mysql_config = {
            "host": os.getenv("MYSQL_OLD_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_OLD_PORT", "3306")),
            "user": os.getenv("MYSQL_OLD_USER", "root"),
            "password": os.getenv("MYSQL_OLD_PASSWORD", ""),
            "database": os.getenv("MYSQL_OLD_DATABASE", "chronoslux"),
            "cursorclass": pymysql.cursors.DictCursor,
            "charset": "utf8mb4",
        }

        self.stdout.write(self.style.WARNING("Conectando a MySQL viejo..."))
        connection = pymysql.connect(**mysql_config)

        try:
            with connection.cursor() as cursor:

                def table_exists(table_name):
                    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
                    return cursor.fetchone() is not None

                tables = [
                    "watches_carrito",
                    "watches_detallecarrito",
                    "watches_domicilio",
                    "watches_envio",
                    "watches_pedido",
                    "watches_detallespedido",
                    "watches_pago",
                    "watches_devolucion",
                ]

                for table in tables:
                    if table_exists(table):
                        cursor.execute(f"SELECT COUNT(*) AS total FROM {table}")
                        total = cursor.fetchone()["total"]
                        self.stdout.write(f"{table}: {total}")
                    else:
                        self.stdout.write(self.style.WARNING(f"No existe: {table}"))

                if options["dry_run"]:
                    self.stdout.write(self.style.SUCCESS("Dry-run terminado. No se migró nada."))
                    return

                # =========================
                # MAPEO USUARIOS
                # =========================
                user_map = {}

                if table_exists("accounts_user"):
                    cursor.execute("SELECT id, email FROM accounts_user")
                    for row in cursor.fetchall():
                        email = (row.get("email") or "").strip().lower()
                        if not email:
                            continue

                        user = User.objects.filter(email=email).first()
                        if user:
                            user_map[row["id"]] = user

                self.stdout.write(self.style.SUCCESS(f"Usuarios mapeados: {len(user_map)}"))

                # =========================
                # MAPEO MARCAS
                # =========================
                marca_map = {}

                if table_exists("watches_marca"):
                    cursor.execute("SELECT id, nombre FROM watches_marca")
                    for row in cursor.fetchall():
                        marca = Marca.objects.filter(nombre=row["nombre"]).first()
                        if marca:
                            marca_map[row["id"]] = marca

                # =========================
                # MAPEO CATEGORÍAS
                # =========================
                categoria_map = {}

                if table_exists("watches_categoria"):
                    cursor.execute("SELECT id, genero, material, tipo FROM watches_categoria")
                    for row in cursor.fetchall():
                        categoria = Categoria.objects.filter(
                            genero=row["genero"],
                            material=row["material"],
                            tipo=row.get("tipo"),
                        ).first()

                        if categoria:
                            categoria_map[row["id"]] = categoria

                # =========================
                # MAPEO PRODUCTOS
                # =========================
                producto_map = {}

                if table_exists("watches_producto"):
                    cursor.execute("SELECT * FROM watches_producto")
                    for row in cursor.fetchall():
                        marca = marca_map.get(row.get("marca_id"))
                        categoria = categoria_map.get(row.get("categoria_id"))

                        if not marca or not categoria:
                            continue

                        producto = Producto.objects.filter(
                            nombre=row["nombre"],
                            marca=marca,
                            categoria=categoria,
                        ).first()

                        if producto:
                            producto_map[row["id"]] = producto

                self.stdout.write(self.style.SUCCESS(f"Productos mapeados: {len(producto_map)}"))

                # =========================
                # MAPEO DOMICILIOS
                # =========================
                domicilio_map = {}

                if table_exists("watches_domicilio"):
                    cursor.execute("SELECT * FROM watches_domicilio")
                    for row in cursor.fetchall():
                        usuario = user_map.get(row.get("usuario_id"))

                        if not usuario:
                            continue

                        domicilio = Domicilio.objects.filter(
                            usuario=usuario,
                            calle=row.get("calle") or "",
                            num_ext=row.get("num_ext") or "",
                            colonia=row.get("colonia") or "",
                            estado=row.get("estado") or "",
                            cp=row.get("cp") or "",
                            pais=row.get("pais") or "",
                        ).first()

                        if domicilio:
                            domicilio_map[row["id"]] = domicilio

                self.stdout.write(self.style.SUCCESS(f"Domicilios mapeados: {len(domicilio_map)}"))

                # =========================
                # MIGRAR CARRITOS
                # =========================
                carrito_map = {}

                if table_exists("watches_carrito"):
                    self.stdout.write(self.style.WARNING("Migrando carritos..."))

                    cursor.execute("SELECT * FROM watches_carrito")
                    for row in cursor.fetchall():
                        usuario = user_map.get(row.get("usuario_id"))

                        if not usuario:
                            continue

                        fecha_creacion = make_aware_if_needed(row.get("fecha_creacion")) or timezone.now()
                        fecha_expiracion = make_aware_if_needed(row.get("fecha_expiracion"))

                        carrito, created = Carrito.objects.get_or_create(
                            usuario=usuario,
                            estado=row.get("estado") or "activo",
                            fecha_creacion=fecha_creacion,
                            defaults={
                                "fecha_expiracion": fecha_expiracion,
                            }
                        )

                        if not created:
                            carrito.fecha_expiracion = fecha_expiracion
                            carrito.save()

                        carrito_map[row["id"]] = carrito

                self.stdout.write(self.style.SUCCESS(f"Carritos mapeados: {len(carrito_map)}"))

                # =========================
                # MIGRAR DETALLE CARRITO
                # =========================
                if table_exists("watches_detallecarrito"):
                    self.stdout.write(self.style.WARNING("Migrando detalles de carrito..."))

                    migrados = 0
                    omitidos = 0

                    cursor.execute("SELECT * FROM watches_detallecarrito")
                    for row in cursor.fetchall():
                        carrito = carrito_map.get(row.get("carrito_id"))
                        producto = producto_map.get(row.get("producto_id"))

                        if not carrito or not producto:
                            omitidos += 1
                            continue

                        DetalleCarrito.objects.get_or_create(
                            carrito=carrito,
                            producto=producto,
                            defaults={
                                "cantidad": row.get("cantidad") or 1,
                                "precio_unitario": money(row.get("precio_unitario")),
                                "subtotal": money(row.get("subtotal")),
                            }
                        )

                        migrados += 1

                    self.stdout.write(self.style.SUCCESS(f"Detalles carrito migrados: {migrados}"))
                    self.stdout.write(self.style.WARNING(f"Detalles carrito omitidos: {omitidos}"))

                # =========================
                # MIGRAR ENVÍOS
                # =========================
                envio_map = {}

                if table_exists("watches_envio"):
                    self.stdout.write(self.style.WARNING("Migrando envíos..."))

                    cursor.execute("SELECT * FROM watches_envio")
                    for row in cursor.fetchall():
                        domicilio = domicilio_map.get(row.get("domicilio_id"))

                        if not domicilio:
                            continue

                        fecha_envio = make_aware_if_needed(row.get("fecha_envio"))
                        fecha_llegada = make_aware_if_needed(row.get("fecha_llegada"))

                        envio, created = Envio.objects.get_or_create(
                            domicilio=domicilio,
                            fecha_envio=fecha_envio,
                            defaults={
                                "fecha_llegada": fecha_llegada,
                            }
                        )

                        if not created:
                            envio.fecha_llegada = fecha_llegada
                            envio.save()

                        envio_map[row["id"]] = envio

                self.stdout.write(self.style.SUCCESS(f"Envíos mapeados: {len(envio_map)}"))

                # =========================
                # MIGRAR PEDIDOS
                # =========================
                pedido_map = {}

                if table_exists("watches_pedido"):
                    self.stdout.write(self.style.WARNING("Migrando pedidos..."))

                    migrados = 0
                    omitidos = 0

                    cursor.execute("SELECT * FROM watches_pedido")
                    for row in cursor.fetchall():
                        usuario = user_map.get(row.get("usuario_id"))
                        carrito = carrito_map.get(row.get("carrito_id"))
                        envio = envio_map.get(row.get("envio_id"))

                        if not usuario:
                            omitidos += 1
                            continue

                        fecha = make_aware_if_needed(row.get("fecha")) or timezone.now()
                        subtotal = money(row.get("subtotal"))
                        total_pagar = money(row.get("total_pagar"))

                        pedido, created = Pedido.objects.get_or_create(
                            usuario=usuario,
                            fecha=fecha,
                            subtotal=subtotal,
                            total_pagar=total_pagar,
                            defaults={
                                "carrito": carrito,
                                "envio": envio,
                            }
                        )

                        if not created:
                            pedido.carrito = carrito
                            pedido.envio = envio
                            pedido.subtotal = subtotal
                            pedido.total_pagar = total_pagar
                            pedido.save()

                        pedido_map[row["id"]] = pedido
                        migrados += 1

                    self.stdout.write(self.style.SUCCESS(f"Pedidos migrados: {migrados}"))
                    self.stdout.write(self.style.WARNING(f"Pedidos omitidos: {omitidos}"))

                # =========================
                # MIGRAR DETALLES PEDIDO
                # =========================
                if table_exists("watches_detallespedido"):
                    self.stdout.write(self.style.WARNING("Migrando detalles de pedido..."))

                    migrados = 0
                    omitidos = 0

                    cursor.execute("SELECT * FROM watches_detallespedido")
                    for row in cursor.fetchall():
                        pedido = pedido_map.get(row.get("pedido_id"))
                        producto = producto_map.get(row.get("producto_id"))

                        if not pedido or not producto:
                            omitidos += 1
                            continue

                        DetallesPedido.objects.get_or_create(
                            pedido=pedido,
                            producto=producto,
                            defaults={
                                "cantidad": row.get("cantidad") or 1,
                                "precio_unitario": money(row.get("precio_unitario")),
                            }
                        )

                        migrados += 1

                    self.stdout.write(self.style.SUCCESS(f"Detalles pedido migrados: {migrados}"))
                    self.stdout.write(self.style.WARNING(f"Detalles pedido omitidos: {omitidos}"))

                # =========================
                # MIGRAR PAGOS
                # =========================
                if table_exists("watches_pago"):
                    self.stdout.write(self.style.WARNING("Migrando pagos..."))

                    migrados = 0
                    omitidos = 0

                    cursor.execute("SELECT * FROM watches_pago")
                    for row in cursor.fetchall():
                        pedido = pedido_map.get(row.get("pedido_id"))

                        if not pedido:
                            omitidos += 1
                            continue

                        Pago.objects.update_or_create(
                            pedido=pedido,
                            defaults={
                                "metodo_pago": row.get("metodo_pago") or "tarjeta",
                                "estado": row.get("estado") or "pendiente",
                                "fecha_pago": make_aware_if_needed(row.get("fecha_pago")),
                                "monto_pagar": money(row.get("monto_pagar")),
                            }
                        )

                        migrados += 1

                    self.stdout.write(self.style.SUCCESS(f"Pagos migrados: {migrados}"))
                    self.stdout.write(self.style.WARNING(f"Pagos omitidos: {omitidos}"))

                # =========================
                # MIGRAR DEVOLUCIONES
                # =========================
                if table_exists("watches_devolucion"):
                    self.stdout.write(self.style.WARNING("Migrando devoluciones..."))

                    migrados = 0
                    omitidos = 0

                    cursor.execute("SELECT * FROM watches_devolucion")
                    for row in cursor.fetchall():
                        pedido = pedido_map.get(row.get("pedido_id"))

                        if not pedido:
                            omitidos += 1
                            continue

                        devolucion, created = Devolucion.objects.get_or_create(
                            pedido=pedido,
                            fecha_devolucion=make_aware_if_needed(row.get("fecha_devolucion")),
                            defaults={
                                "url_img_prod_devuelto": row.get("url_img_prod_devuelto"),
                                "descripcion_devolucion": row.get("descripcion_devolucion"),
                                "estado": row.get("estado") or "solicitada",
                            }
                        )

                        if not created:
                            devolucion.url_img_prod_devuelto = row.get("url_img_prod_devuelto")
                            devolucion.descripcion_devolucion = row.get("descripcion_devolucion")
                            devolucion.estado = row.get("estado") or "solicitada"
                            devolucion.save()

                        migrados += 1

                    self.stdout.write(self.style.SUCCESS(f"Devoluciones migradas: {migrados}"))
                    self.stdout.write(self.style.WARNING(f"Devoluciones omitidas: {omitidos}"))

        finally:
            connection.close()

        self.stdout.write(self.style.SUCCESS("Migración de ventas/pedidos terminada."))

