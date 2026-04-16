from django.contrib.auth.models import AbstractUser
from django.db import models


from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    # 🔥 doctor extra fields
    full_name = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=100, blank=True)