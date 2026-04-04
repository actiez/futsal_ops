from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_USER = "user"
    ROLE_ADMIN = "admin"
    ROLE_SUPERADMIN = "superadmin"

    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ADMIN, "Admin"),
        (ROLE_SUPERADMIN, "Superadmin"),
    ]

    PLAYER_NEW = "new"
    PLAYER_REGULAR = "regular"
    PLAYER_CORE = "core"
    PLAYER_NAUGHTY = "naughty"

    PLAYER_TYPE_CHOICES = [
        (PLAYER_NEW, "New"),
        (PLAYER_REGULAR, "Regular"),
        (PLAYER_CORE, "Core"),
        (PLAYER_NAUGHTY, "Naughty"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    player_type = models.CharField(max_length=20, choices=PLAYER_TYPE_CHOICES, default=PLAYER_NEW)
    mobile_number = models.CharField(max_length=30, blank=True)
    games_played_count = models.PositiveIntegerField(default=0)
    email_verified = models.BooleanField(default=False)

    def is_admin_level(self):
        return self.is_authenticated and (
            self.is_superuser or self.role in {self.ROLE_ADMIN, self.ROLE_SUPERADMIN}
        ) 

    def is_superadmin_level(self):
        return self.is_authenticated and (
            self.is_superuser or self.role == self.ROLE_SUPERADMIN
        )