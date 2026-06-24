import os
from decimal import Decimal

import pymysql
from django.core.management.base import BaseCommand
from django.utils import timezone
from dotenv import load_dotenv

from accounts.models import User
from watches.models import Marca, Categoria, Producto
from proveedores.models import Proveedor, Compra, DetalleCompra


def make_aware_if_needed(value):
    if value is None:
        return None

    if timezone.is_naive(value):
        return timezone.make_aware(value)

    return value


class Command(BaseCommand):
    help = "Migra proveedores, compras y detalles de compra desde MySQL viejo a MongoDB."

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

                required_tables = [
                    "accounts_user",
                    "watches_marca",
                    "watches_categoria",
                    "watches_producto",
                    "proveedores_proveedor",
                    "proveedores_compra",
                    "proveedores_detallecompra",
                ]

                for table in required_tables:
                    if not table_exists(table):
                        raise Exception(f"No existe la tabla requerida en MySQL: {table}")

                cursor.execute("SELECT COUNT(*) AS total FROM proveedores_proveedor")
                total_proveedores = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM proveedores_compra")
                total_compras = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM proveedores_detallecompra")
                total_detalles = cursor.fetchone()["total"]

                self.stdout.write(f"Proveedores en MySQL: {total_proveedores}")
                self.stdout.write(f"Compras en MySQL: {total_compras}")
                self.stdout.write(f"Detalles de compra en MySQL: {total_detalles}")

                if options["dry_run"]:
                    self.stdout.write(self.style.SUCCESS("Dry-run terminado. No se migró nada."))
                    return

                # Mapeo usuario viejo -> usuario Mongo
                user_map = {}
                cursor.execute("SELECT id, email FROM accounts_user")
                for row in cursor.fetchall():
                    email = (row.get("email") or "").strip().lower()
                    if not email:
                        continue

                    user = User.objects.filter(email=email).first()
                    if user:
                        user_map[row["id"]] = user

                self.stdout.write(self.style.SUCCESS(f"Usuarios mapeados: {len(user_map)}"))

                # Mapeo marca vieja -> marca Mongo
                marca_map = {}
                cursor.execute("SELECT id, nombre FROM watches_marca")
                for row in cursor.fetchall():
                    marca = Marca.objects.filter(nombre=row["nombre"]).first()
                    if marca:
                        marca_map[row["id"]] = marca

                # Mapeo categoría vieja -> categoría Mongo
                categoria_map = {}
                cursor.execute("SELECT id, genero, material, tipo FROM watches_categoria")
                for row in cursor.fetchall():
                    categoria = Categoria.objects.filter(
                        genero=row["genero"],
                        material=row["material"],
                        tipo=row.get("tipo"),
                    ).first()

                    if categoria:
                        categoria_map[row["id"]] = categoria

                # Mapeo producto viejo -> producto Mongo
                producto_map = {}
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

                # Migrar proveedores
                proveedor_map = {}
                proveedores_migrados = 0
                proveedores_omitidos = 0

                self.stdout.write(self.style.WARNING("Migrando proveedores..."))

                cursor.execute("SELECT * FROM proveedores_proveedor")
                for row in cursor.fetchall():
                    user = user_map.get(row.get("user_id"))

                    if not user:
                        proveedores_omitidos += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"Proveedor omitido porque no se encontró usuario viejo ID: {row.get('user_id')}"
                            )
                        )
                        continue

                    proveedor, created = Proveedor.objects.get_or_create(
                        user=user,
                        defaults={
                            "nombre_empresa": row.get("nombre_empresa") or "",
                            "telefono_contacto": row.get("telefono_contacto") or "",
                            "direccion": row.get("direccion") or "",
                            "fecha_creacion": make_aware_if_needed(row.get("fecha_creacion")) or timezone.now(),
                        }
                    )

                    if not created:
                        proveedor.nombre_empresa = row.get("nombre_empresa") or proveedor.nombre_empresa
                        proveedor.telefono_contacto = row.get("telefono_contacto") or ""
                        proveedor.direccion = row.get("direccion") or ""
                        proveedor.fecha_creacion = make_aware_if_needed(row.get("fecha_creacion")) or proveedor.fecha_creacion
                        proveedor.save()

                    proveedor_map[row["id"]] = proveedor
                    proveedores_migrados += 1

                self.stdout.write(self.style.SUCCESS(f"Proveedores migrados: {proveedores_migrados}"))
                self.stdout.write(self.style.WARNING(f"Proveedores omitidos: {proveedores_omitidos}"))

                # Migrar compras
                compra_map = {}
                compras_migradas = 0
                compras_omitidas = 0

                self.stdout.write(self.style.WARNING("Migrando compras..."))

                cursor.execute("SELECT * FROM proveedores_compra")
                for row in cursor.fetchall():
                    proveedor = proveedor_map.get(row.get("proveedor_id"))

                    if not proveedor:
                        compras_omitidas += 1
                        continue

                    fecha_compra = make_aware_if_needed(row.get("fecha_compra")) or timezone.now()
                    total_compra = Decimal(str(row.get("total_compra") or "0"))

                    compra, created = Compra.objects.get_or_create(
                        proveedor=proveedor,
                        fecha_compra=fecha_compra,
                        defaults={
                            "total_compra": total_compra,
                        }
                    )

                    if not created:
                        compra.total_compra = total_compra
                        compra.save()

                    compra_map[row["id"]] = compra
                    compras_migradas += 1

                self.stdout.write(self.style.SUCCESS(f"Compras migradas: {compras_migradas}"))
                self.stdout.write(self.style.WARNING(f"Compras omitidas: {compras_omitidas}"))

                # Migrar detalles de compra
                detalles_migrados = 0
                detalles_omitidos = 0

                self.stdout.write(self.style.WARNING("Migrando detalles de compra..."))

                cursor.execute("SELECT * FROM proveedores_detallecompra")
                for row in cursor.fetchall():
                    compra = compra_map.get(row.get("compra_id"))
                    producto = producto_map.get(row.get("producto_id"))

                    if not compra or not producto:
                        detalles_omitidos += 1
                        continue

                    cantidad = row.get("cantidad") or 0
                    costo_unitario = Decimal(str(row.get("costo_unitario") or "0"))

                    detalle, created = DetalleCompra.objects.get_or_create(
                        compra=compra,
                        producto=producto,
                        defaults={
                            "cantidad": cantidad,
                            "costo_unitario": costo_unitario,
                        }
                    )

                    if not created:
                        detalle.cantidad = cantidad
                        detalle.costo_unitario = costo_unitario
                        detalle.save()

                    detalles_migrados += 1

                self.stdout.write(self.style.SUCCESS(f"Detalles migrados: {detalles_migrados}"))
                self.stdout.write(self.style.WARNING(f"Detalles omitidos: {detalles_omitidos}"))

        finally:
            connection.close()

        self.stdout.write(self.style.SUCCESS("Migración de proveedores terminada."))

