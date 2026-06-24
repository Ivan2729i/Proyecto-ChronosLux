import os
import pymysql

from django.core.management.base import BaseCommand
from django.utils import timezone
from dotenv import load_dotenv

from accounts.models import User
from watches.models import Domicilio


def make_aware_if_needed(value):
    if value is None:
        return None

    if timezone.is_naive(value):
        return timezone.make_aware(value)

    return value


def to_bool(value):
    return value in (True, 1, "1", "true", "True", "TRUE")


class Command(BaseCommand):
    help = "Migra usuarios y domicilios desde MySQL viejo a MongoDB."

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

                if not table_exists("accounts_user"):
                    raise Exception("No existe la tabla accounts_user en MySQL.")

                cursor.execute("SELECT COUNT(*) AS total FROM accounts_user")
                total_usuarios = cursor.fetchone()["total"]

                total_domicilios = 0
                if table_exists("watches_domicilio"):
                    cursor.execute("SELECT COUNT(*) AS total FROM watches_domicilio")
                    total_domicilios = cursor.fetchone()["total"]

                self.stdout.write(f"Usuarios en MySQL: {total_usuarios}")
                self.stdout.write(f"Domicilios en MySQL: {total_domicilios}")

                if options["dry_run"]:
                    self.stdout.write(self.style.SUCCESS("Dry-run terminado. No se migró nada."))
                    return

                user_map = {}

                self.stdout.write(self.style.WARNING("Migrando usuarios..."))

                cursor.execute("SELECT * FROM accounts_user")
                for row in cursor.fetchall():
                    email = (row.get("email") or "").strip().lower()

                    if not email:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Usuario omitido porque no tiene email. ID viejo: {row.get('id')}"
                            )
                        )
                        continue

                    username = row.get("username") or email.split("@")[0]

                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            "username": username,
                            "first_name": row.get("first_name") or "",
                            "last_name": row.get("last_name") or "",
                            "password": row.get("password") or "",
                            "is_superuser": to_bool(row.get("is_superuser")),
                            "is_staff": to_bool(row.get("is_staff")),
                            "is_active": to_bool(row.get("is_active")),
                            "last_login": make_aware_if_needed(row.get("last_login")),
                            "date_joined": make_aware_if_needed(row.get("date_joined")) or timezone.now(),
                        }
                    )

                    if not created:
                        user.username = username
                        user.first_name = row.get("first_name") or ""
                        user.last_name = row.get("last_name") or ""
                        user.is_active = to_bool(row.get("is_active"))

                        if row.get("password"):
                            user.password = row.get("password")

                        if row.get("last_login"):
                            user.last_login = make_aware_if_needed(row.get("last_login"))

                        user.save()

                    user_map[row["id"]] = user

                self.stdout.write(self.style.SUCCESS(f"Usuarios migrados/mapeados: {len(user_map)}"))

                if not table_exists("watches_domicilio"):
                    self.stdout.write(self.style.WARNING("No existe watches_domicilio. Se omite domicilios."))
                    return

                self.stdout.write(self.style.WARNING("Migrando domicilios..."))

                cursor.execute("SELECT * FROM watches_domicilio")
                domicilios_migrados = 0

                for row in cursor.fetchall():
                    usuario = user_map.get(row.get("usuario_id"))

                    if not usuario:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Domicilio omitido porque no se encontró usuario viejo ID: {row.get('usuario_id')}"
                            )
                        )
                        continue

                    Domicilio.objects.get_or_create(
                        usuario=usuario,
                        calle=row.get("calle") or "",
                        num_ext=row.get("num_ext") or "",
                        colonia=row.get("colonia") or "",
                        estado=row.get("estado") or "",
                        cp=row.get("cp") or "",
                        pais=row.get("pais") or "",
                        defaults={
                            "telefono": row.get("telefono"),
                            "num_int": row.get("num_int"),
                        }
                    )

                    domicilios_migrados += 1

                self.stdout.write(self.style.SUCCESS(f"Domicilios migrados: {domicilios_migrados}"))

        finally:
            connection.close()

        self.stdout.write(self.style.SUCCESS("Migración de usuarios y domicilios terminada."))

