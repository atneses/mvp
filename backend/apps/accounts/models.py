"""Custom user: Django's user plus a role and the countries it can work with."""

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ANALYST = "analyst", "Analyst"
        ADMIN = "admin", "Admin"

    # Least privilege by default: new users are analysts.
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.ANALYST)

    allowed_countries = ArrayField(models.CharField(max_length=2), default=list, blank=True)

    def can_access_country(self, country: str) -> bool:
        # Admins are scoped too: they only see the countries they were given.
        return country in self.allowed_countries
