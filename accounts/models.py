from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'                       # login con email
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']  # para createsuperuser

    def __str__(self):
        return self.email
