from uuid import uuid4
from django.db.models import (
    Model,
    CharField,
    PositiveIntegerField,
    UUIDField,
    BooleanField,
    DateTimeField,
    TextChoices,
    ForeignKey,
    CASCADE
)
#from .services import buy_futures_contract
from django.core.validators import MinValueValidator
from trader.models import ExchangeAccount
from exchange.models import WalletPair


class TradeType(TextChoices):
    LONG = "LONG", "Лонг"
    SHORT = "SHORT", "Шорт"


class Entry(Model):
    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор ",
        primary_key=True,
        verbose_name="ID",
    )
    profit = PositiveIntegerField(
        validators=[MinValueValidator(1)], 
        blank = True,
        null = True,
        help_text="Маржа",
        verbose_name="Маржа"
    )
    shoulder = PositiveIntegerField(
        help_text="Плечо",
        verbose_name="Плечо",
        blank = True
    )
    count = PositiveIntegerField(
        help_text="Количество",
        verbose_name="Количество"
    )
    exit_course = PositiveIntegerField(
        help_text="Курс выхода",
        verbose_name="Курс выхода"
    )
    wallet_pair = ForeignKey(
        WalletPair,
        on_delete=CASCADE,
        related_name="entry_wallet_pair",
        verbose_name="Валютная пара",
    )
    is_active = BooleanField(
        default=True,
        help_text="Активность",
        verbose_name="Активность"
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text="Дата создания",
        verbose_name="Дата создания",
    )
    class Meta:
        db_table = "entry"
        verbose_name = "Вход"
        verbose_name_plural = "Входы"
        ordering = ("-created_at",)

    def __str__(self):
        return f'{self.profit}'


class Order(Model):
    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор ",
        primary_key=True,
        verbose_name="ID",
    )
    entry_course = PositiveIntegerField(
        help_text="Курс входа",
        verbose_name="Курс входа"
    )
    trade_type = CharField(
        choices=TradeType.choices,
        help_text="Тип сделки",
        verbose_name="Тип сделки",
    )
    entry = ForeignKey(
        Entry,
        on_delete=CASCADE,
        related_name="order_entry",
        verbose_name="Вход",
    )
    exchange_account = ForeignKey(
        ExchangeAccount,
        on_delete=CASCADE,
        related_name="order_exchange_account",
        verbose_name="Биржевый аккаунт",
    )
    class Meta:
        db_table = "order"
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ("-trade_type",)

    def __str__(self):
        return f'{self.entry_course}'
