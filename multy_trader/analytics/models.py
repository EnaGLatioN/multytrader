from uuid import uuid4
from django.db.models import (
    Model,
    CharField,
    FloatField,
    PositiveIntegerField,
    UUIDField,
    DateTimeField,
    TextChoices,
    ForeignKey,
    CASCADE,
    SET_NULL,
    BigIntegerField,
    BooleanField,
    TextField,
    ManyToManyField
)
from django.conf import settings
from trader.models import ExchangeAccount, Proxy
from exchange.models import WalletPair, Exchange
from trade.models import Entry

class StatusType(TextChoices):
    COMPLETED = "COMPLETED", "Завершено"
    STOPPED = "STOPPED", "Остановлен"
    FAILED = "FAILED", "Завершен с ошибкой"


class Analytics(Model):
    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор ",
        primary_key=True,
        verbose_name="ID",
    )
    trader = ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=CASCADE, 
        related_name='analytics',
        verbose_name='Трейдер',
        null=True, 
        blank=True
    )
    status = CharField(
        choices=StatusType.choices,
        default=StatusType.COMPLETED.value,
        null=True, 
        blank=True,
        max_length = 50,
        help_text="Статус",
        verbose_name="Статус",
    )
    entry = ForeignKey(
        Entry, 
        on_delete=SET_NULL, 
        null=True, 
        blank=True,
        related_name='analytics_entry'
    )
    wallet_pair = ForeignKey(
        WalletPair,
        on_delete=CASCADE,
        null=True, 
        blank=True,
        related_name="analytics_wallet_pair",
        verbose_name="Валютная пара",
    )
    profit = FloatField(
        blank = True,
        null = True,
        help_text="Колличество монет",
        verbose_name="Колличество монет"
    )
    shoulder = PositiveIntegerField(
        help_text="Плечо",
        verbose_name="Плечо"
    )
    exchange_long = ManyToManyField(
        Exchange,
        blank=True,
        related_name="long_exchange",
        verbose_name="Биржа лонг",
    )
    exchange_short = ManyToManyField(
        Exchange,
        blank=True,
        related_name="short_exchange",
        verbose_name="Биржа шорт",
    )
    target_entry_spread = FloatField(
        blank = True,
        null = True,
        help_text="Указанный спред входа",
        verbose_name="Указанный спред входа"
    )
    actual_entry_spread = FloatField(
        blank = True,
        null = True,
        help_text="Реальный спред входа",
        verbose_name="Реальный спред входа"
    )
    target_exit_spread = FloatField(
        blank = True,
        null = True,
        help_text="Указанный спред выхода",
        verbose_name="Указанный спред выхода"
    )
    actual_exit_spread = FloatField(
        blank = True,
        null = True,
        help_text="Реальный спред выхода",
        verbose_name="Реальный спред выхода"
    )
    pnl_percent = FloatField(
        blank = True,
        null = True,
        help_text="PNL %",
        verbose_name="PNL %"
    )
    pnl_currency = FloatField(
        blank = True,
        null = True,
        help_text="PNL $",
        verbose_name="PNL $"
    )
    start_time = DateTimeField(
        blank=True,
        null=True,
        help_text="Время входа",
        verbose_name="Время входа"
    )
    exit_time = DateTimeField(
        blank=True,
        null=True,
        help_text="Время выхода",
        verbose_name="Время выхода"
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text="Дата создания",
        verbose_name="Дата создания",
    )

    class Meta:
        db_table = "analytics"
        verbose_name = "Аналитика"
        verbose_name_plural = "Аналитика"
        ordering = ("-created_at",)
