from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("USER", "User"),
        ("TEACHER", "Teacher"),
        ("ADMIN", "Admin")
    ]
    username = models.CharField(max_length=64, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="USER")

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"