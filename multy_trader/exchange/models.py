from uuid import uuid4
from django.db.models import (
    Model,
    CharField,
    DateTimeField,
    UUIDField,
    ManyToManyField
)
from django.db import models


class WalletPair(Model):
    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор ",
        primary_key=True,
        verbose_name="ID",
    )
    slug = CharField(
        "Слаг пары",
        max_length=255,
        help_text="Слаг пары",
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text="Дата создания",
        verbose_name="Дата создания",
    )
    class Meta:
        db_table = "walet_pair"
        verbose_name = "Валютная пара"
        verbose_name_plural = "Валютные пары"
        ordering = ("slug",)

    def __str__(self):
        return self.slug


class Exchange(Model):
    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор ",
        primary_key=True,
        verbose_name="ID",
    )
    name = CharField(
        "Название биржи",
        max_length=255,
        help_text="Название биржи",
    )
    wallet_pairs = ManyToManyField(
        WalletPair,
        related_name="exchange_wallet_pair",
        verbose_name="Валютные пары",
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text="Дата создания",
        verbose_name="Дата создания",
    )
    class Meta:
        db_table = "exchange"
        verbose_name = "Биржа"
        verbose_name_plural = "Биржи"
        ordering = ("name",)

    def __str__(self):
        return self.name