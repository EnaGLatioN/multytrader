from uuid import uuid4
from django.db.models import (
    Model,
    CharField,
    DateTimeField,
    UUIDField,
    ManyToManyField,
    PositiveIntegerField,
    BooleanField,
    ForeignKey,
    CASCADE
)


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
    is_active = BooleanField(
        default=True,
        help_text="Активна ли валютная пара",
        verbose_name="Активность"
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text="Дата создания",
        verbose_name="Дата создания",
    )

    class Meta:
        db_table = "wallet_pair"
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
    max_limit = PositiveIntegerField(
        help_text="Максимальное кол-во",
        verbose_name="Максимальное кол-во",
        default=0
    )
    min_limit = PositiveIntegerField(
        help_text="Минимальное кол-во",
        verbose_name="Минимальное кол-во",
        default = 0
    )
    base_url = CharField(
        max_length=255,
        default=""
    )
    api_endpoint = CharField(
        max_length=255,
        default=""
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

class PairExchangeMapping(Model):
    wallet_pair = ForeignKey(
        WalletPair,
        blank=True, 
        null=True,
        on_delete=CASCADE, 
        related_name="exchange_mappings", 
        verbose_name="Единая пара"
    )
    exchange = ForeignKey(
        Exchange, 
        on_delete=CASCADE, 
        related_name="pair_mappings", 
        verbose_name="Биржа"
    )
    local_name = CharField(
        max_length=50, 
        verbose_name="Локальное имя на бирже"
    )
    coin_count = PositiveIntegerField(
        help_text="Кол-во монет в контракте",
        verbose_name="Кол-во монет в контракте",
        default = 0
    )

    class Meta:
        verbose_name = "Маппинг пары на биржу"
        verbose_name_plural = "Маппинги пар на биржи"
        unique_together = ['wallet_pair', 'exchange']
        ordering = ['wallet_pair', 'exchange']

    def __str__(self):
        return f"{self.local_name}"