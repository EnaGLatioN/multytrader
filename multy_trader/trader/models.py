from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class CustomUser(AbstractUser):
    walet_pairs_gate = models.ManyToManyField(
        'gate.WaletPairs',  # Исправлено на правильный формат
        related_name='users',
        verbose_name='Валютные пары',
        blank=True
    )
    walet_pairs_mexc = models.ManyToManyField(
        'mexc.WaletPairsMexc',  # Исправлено на правильный формат
        related_name='users_mexc',
        verbose_name='Валютные пары',
        blank=True
    )
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        verbose_name='Группы',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        verbose_name='Разрешения',
        blank=True,
    )
