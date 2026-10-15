"""Create or reset the demo users. Safe to run many times."""

import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User

DEMO_USERS = [
    {"username": "analyst_es", "role": User.Role.ANALYST, "allowed_countries": ["ES"]},
    {"username": "analyst_mx", "role": User.Role.ANALYST, "allowed_countries": ["MX"]},
    {"username": "admin", "role": User.Role.ADMIN, "allowed_countries": ["ES", "MX"]},
]


class Command(BaseCommand):
    help = "Create the demo users (analyst_es, analyst_mx, admin)."

    def handle(self, *args, **options):
        # Never hardcoded: the repository is public.
        password = os.environ.get("SEED_USERS_PASSWORD")
        if not password:
            raise CommandError("SEED_USERS_PASSWORD is not set.")

        with transaction.atomic():
            for data in DEMO_USERS:
                user, created = User.objects.update_or_create(
                    username=data["username"],
                    defaults={
                        "role": data["role"],
                        "allowed_countries": data["allowed_countries"],
                    },
                )
                # Reset the password on every run so it always matches the env var.
                user.set_password(password)
                user.save(update_fields=["password"])
                self.stdout.write(f"{'created' if created else 'updated'}: {user.username}")
