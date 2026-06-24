import os
from decimal import Decimal

import pymysql
from django.core.management.base import BaseCommand
from django.utils import timezone
from dotenv import load_dotenv

from watches.models import Marca, Categoria, Producto, ImgProducto


def make_aware_if_needed(value):
    if value is None:
        return None

    if timezone.is_naive(value):
        return timezone.make_aware(value)

    return value


def to_bool(value):
    if value in (True, 1, "1", "true", "True", "TRUE"):
        return True
    return False


class Command(BaseCommand):
    help = "Migra Marca, Categoria, Producto e ImgProducto desde MySQL viejo a MongoDB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra conteos, no migra datos."
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Borra catálogo actual en Mongo antes de migrar."
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
                    "watches_marca",
                    "watches_categoria",
                    "watches_producto",
                    "watches_imgproducto",
                ]

                for table in required_tables:
                    if not table_exists(table):
                        raise Exception(f"No existe la tabla requerida en MySQL: {table}")

                cursor.execute("SELECT COUNT(*) AS total FROM watches_marca")
                total_marcas = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM watches_categoria")
                total_categorias = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM watches_producto")
                total_productos = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM watches_imgproducto")
                total_imagenes = cursor.fetchone()["total"]

                self.stdout.write(f"Marcas en MySQL: {total_marcas}")
                self.stdout.write(f"Categorías en MySQL: {total_categorias}")
                self.stdout.write(f"Productos en MySQL: {total_productos}")
                self.stdout.write(f"Imágenes en MySQL: {total_imagenes}")

                if options["dry_run"]:
                    self.stdout.write(self.style.SUCCESS("Dry-run terminado. No se migró nada."))
                    return

                if options["clear"]:
                    self.stdout.write(self.style.WARNING("Borrando catálogo actual en MongoDB..."))
                    ImgProducto.objects.all().delete()
                    Producto.objects.all().delete()
                    Categoria.objects.all().delete()
                    Marca.objects.all().delete()

                marca_map = {}
                categoria_map = {}
                producto_map = {}

                self.stdout.write(self.style.WARNING("Migrando marcas..."))

                cursor.execute("SELECT * FROM watches_marca")
                for row in cursor.fetchall():
                    marca, _ = Marca.objects.get_or_create(
                        nombre=row["nombre"]
                    )
                    marca_map[row["id"]] = marca

                self.stdout.write(self.style.SUCCESS(f"Marcas migradas: {len(marca_map)}"))

                self.stdout.write(self.style.WARNING("Migrando categorías..."))

                cursor.execute("SELECT * FROM watches_categoria")
                for row in cursor.fetchall():
                    categoria, _ = Categoria.objects.get_or_create(
                        genero=row["genero"],
                        material=row["material"],
                        tipo=row.get("tipo"),
                    )
                    categoria_map[row["id"]] = categoria

                self.stdout.write(self.style.SUCCESS(f"Categorías migradas: {len(categoria_map)}"))

                self.stdout.write(self.style.WARNING("Migrando productos..."))

                cursor.execute("SELECT * FROM watches_producto")
                for row in cursor.fetchall():
                    marca = marca_map.get(row["marca_id"])
                    categoria = categoria_map.get(row["categoria_id"])

                    if not marca or not categoria:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Producto omitido por marca/categoría faltante: {row['nombre']}"
                            )
                        )
                        continue

                    producto, created = Producto.objects.get_or_create(
                        nombre=row["nombre"],
                        marca=marca,
                        categoria=categoria,
                        defaults={
                            "precio": Decimal(str(row["precio"])),
                            "descripcion1": row.get("descripcion1"),
                            "descripcion2": row.get("descripcion2"),
                            "descripcion3": row.get("descripcion3"),
                            "stock": row.get("stock") or 0,
                            "es_exclusivo": to_bool(row.get("es_exclusivo")),
                            "fecha_borrado": make_aware_if_needed(row.get("fecha_borrado")),
                            "fecha_creacion": make_aware_if_needed(row.get("fecha_creacion")),
                            "fecha_actualizacion": make_aware_if_needed(row.get("fecha_actualizacion")),
                        }
                    )

                    if not created:
                        producto.precio = Decimal(str(row["precio"]))
                        producto.descripcion1 = row.get("descripcion1")
                        producto.descripcion2 = row.get("descripcion2")
                        producto.descripcion3 = row.get("descripcion3")
                        producto.stock = row.get("stock") or 0
                        producto.es_exclusivo = to_bool(row.get("es_exclusivo"))
                        producto.fecha_borrado = make_aware_if_needed(row.get("fecha_borrado"))
                        producto.fecha_creacion = make_aware_if_needed(row.get("fecha_creacion"))
                        producto.fecha_actualizacion = make_aware_if_needed(row.get("fecha_actualizacion"))
                        producto.save()

                    producto_map[row["id"]] = producto

                self.stdout.write(self.style.SUCCESS(f"Productos migrados: {len(producto_map)}"))

                self.stdout.write(self.style.WARNING("Migrando imágenes..."))

                cursor.execute("SELECT * FROM watches_imgproducto")
                imagenes_migradas = 0

                for row in cursor.fetchall():
                    producto = producto_map.get(row["producto_id"])

                    if not producto:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Imagen omitida por producto faltante. ID viejo producto: {row['producto_id']}"
                            )
                        )
                        continue

                    url = row.get("url")
                    if not url:
                        continue

                    ImgProducto.objects.update_or_create(
                        producto=producto,
                        defaults={
                            "url": url,
                            "fecha_creacion": make_aware_if_needed(row.get("fecha_creacion")),
                        }
                    )

                    imagenes_migradas += 1

                self.stdout.write(self.style.SUCCESS(f"Imágenes migradas: {imagenes_migradas}"))

        finally:
            connection.close()

        self.stdout.write(self.style.SUCCESS("Migración de catálogo terminada."))

