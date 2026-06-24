import os
import pymysql

from django.core.management.base import BaseCommand
from django.utils import timezone
from dotenv import load_dotenv

from accounts.models import User
from watches.models import (
    Marca,
    Categoria,
    Producto,
    Favorito,
    Resena,
)


def make_aware_if_needed(value):
    if value is None:
        return None

    if timezone.is_naive(value):
        return timezone.make_aware(value)

    return value


class Command(BaseCommand):
    help = "Migra favoritos y reseñas desde MySQL viejo a MongoDB."

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

                has_favoritos = table_exists("watches_favorito")
                has_resenas = table_exists("watches_resena")

                if not has_favoritos and not has_resenas:
                    raise Exception("No existen watches_favorito ni watches_resena en MySQL.")

                total_favoritos = 0
                total_resenas = 0

                if has_favoritos:
                    cursor.execute("SELECT COUNT(*) AS total FROM watches_favorito")
                    total_favoritos = cursor.fetchone()["total"]

                if has_resenas:
                    cursor.execute("SELECT COUNT(*) AS total FROM watches_resena")
                    total_resenas = cursor.fetchone()["total"]

                self.stdout.write(f"Favoritos en MySQL: {total_favoritos}")
                self.stdout.write(f"Reseñas en MySQL: {total_resenas}")

                if options["dry_run"]:
                    self.stdout.write(self.style.SUCCESS("Dry-run terminado. No se migró nada."))
                    return

                # Map usuario viejo -> usuario Mongo
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

                # Map marca vieja -> marca Mongo
                marca_map = {}

                if table_exists("watches_marca"):
                    cursor.execute("SELECT id, nombre FROM watches_marca")
                    for row in cursor.fetchall():
                        marca = Marca.objects.filter(nombre=row["nombre"]).first()
                        if marca:
                            marca_map[row["id"]] = marca

                # Map categoría vieja -> categoría Mongo
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

                # Map producto viejo -> producto Mongo
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

                # Migrar favoritos
                favoritos_migrados = 0
                favoritos_omitidos = 0

                if has_favoritos:
                    self.stdout.write(self.style.WARNING("Migrando favoritos..."))

                    cursor.execute("SELECT * FROM watches_favorito")
                    for row in cursor.fetchall():
                        usuario = user_map.get(row.get("usuario_id"))
                        producto = producto_map.get(row.get("producto_id"))

                        if not usuario or not producto:
                            favoritos_omitidos += 1
                            continue

                        Favorito.objects.get_or_create(
                            usuario=usuario,
                            producto=producto,
                            defaults={
                                "fecha": make_aware_if_needed(row.get("fecha")) or timezone.now()
                            }
                        )

                        favoritos_migrados += 1

                self.stdout.write(self.style.SUCCESS(f"Favoritos migrados: {favoritos_migrados}"))
                self.stdout.write(self.style.WARNING(f"Favoritos omitidos: {favoritos_omitidos}"))

                # Migrar reseñas
                resenas_migradas = 0
                resenas_omitidas = 0

                if has_resenas:
                    self.stdout.write(self.style.WARNING("Migrando reseñas..."))

                    cursor.execute("SELECT * FROM watches_resena")
                    for row in cursor.fetchall():
                        usuario = user_map.get(row.get("usuario_id"))
                        producto = producto_map.get(row.get("producto_id"))

                        if not usuario or not producto:
                            resenas_omitidas += 1
                            continue

                        fecha = make_aware_if_needed(row.get("fecha")) or timezone.now()

                        resena, created = Resena.objects.get_or_create(
                            usuario=usuario,
                            producto=producto,
                            defaults={
                                "calificacion": row.get("calificacion") or 0,
                                "comentario": row.get("comentario"),
                                "fecha": fecha,
                            }
                        )

                        if not created:
                            resena.calificacion = row.get("calificacion") or resena.calificacion
                            resena.comentario = row.get("comentario")
                            resena.fecha = fecha
                            resena.save()

                        resenas_migradas += 1

                self.stdout.write(self.style.SUCCESS(f"Reseñas migradas: {resenas_migradas}"))
                self.stdout.write(self.style.WARNING(f"Reseñas omitidas: {resenas_omitidas}"))

        finally:
            connection.close()

        self.stdout.write(self.style.SUCCESS("Migración de favoritos y reseñas terminada."))

