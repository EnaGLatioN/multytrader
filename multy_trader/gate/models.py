from uuid import uuid4
from django.db.models import (
    CharField,
    DateTimeField,
    UUIDField,
)
from django.db import models


class WaletPairs(models.Model):
    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор",
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
        db_table = "walet_pairs"
        verbose_name = "Валютная пара."
        verbose_name_plural = "Валютные пары"
        ordering = ("-created_at",)

    def __str__(self):
        return self.slug


class OrderBook(models.Model):
    symbol = models.CharField(max_length=10, default='BTC_USDT')
    current_bid = models.FloatField()
    current_ask = models.FloatField()
    spread = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)
    created_at = DateTimeField(
        auto_now_add=True,
        help_text="Дата создания",
        verbose_name="Дата создания",
    )

    class Meta:
        db_table = "order_book"
        verbose_name = "Стакан."
        verbose_name_plural = "Стаканы."
        ordering = ("-created_at",)

    def __str__(self):
        return f'{self.symbol} - Bid: {self.current_bid}, Ask: {self.current_ask}, Spread: {self.spread}'