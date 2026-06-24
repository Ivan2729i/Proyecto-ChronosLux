from django.apps import AppConfig


class WatchesConfig(AppConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
    name = "watches"