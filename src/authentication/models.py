from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser

from .managers import CustomUserManager


class User(AbstractUser):
    ROLE_CHOICES = [
        ("USER", "User"),
        ("TEACHER", "Teacher"),
        ("ADMIN", "Admin")
    ]

    username = models.CharField(max_length=64, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="USER")

    # is_active = models.BooleanField(default=True)
    # is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']