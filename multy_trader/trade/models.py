from uuid import uuid4
from django.db.models import (
    Model,
    CharField,
    PositiveIntegerField,
    UUIDField,
    DateTimeField,
    TextChoices,
    ForeignKey,
    CASCADE
)
from django.core.validators import MinValueValidator
from trader.models import ExchangeAccount, Proxy
from exchange.models import WalletPair


class EntryStatusType(TextChoices):
    WAIT = "WAIT", "В Ожидании"
    ACTIVE = "ACTIVE", "Активно"
    COMPLETED = "COMPLETED", "Завершено"


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
        help_text="Колличество монет",
        verbose_name="Колличество монет"
    )
    shoulder = PositiveIntegerField(
        help_text="Плечо",
        verbose_name="Плечо",
        blank = True
    )
    status = CharField(
        choices=EntryStatusType.choices,
        default=EntryStatusType.WAIT.value,
        help_text="Статус",
        verbose_name="Статус",
    )
    exit_course = PositiveIntegerField(
        help_text="Курс выхода",
        verbose_name="Курс выхода"
    )
    entry_course = PositiveIntegerField(
        help_text="Курс входа",
        verbose_name="Курс входа"
    )
    wallet_pair = ForeignKey(
        WalletPair,
        on_delete=CASCADE,
        related_name="entry_wallet_pair",
        verbose_name="Валютная пара",
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
    proxy = ForeignKey(
        Proxy,
        on_delete=CASCADE,
        related_name="order_proxy",
        verbose_name="Прокси",
    )
    class Meta:
        db_table = "order"
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f'{self.id}'



class Process(Model):
    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор ",
        primary_key=True,
        verbose_name="ID",
    )
    pid = PositiveIntegerField(
        help_text="Пид процесса",
        verbose_name="Пид процесса"
    )
    entry_id = CharField(
        blank=True,
        help_text="ID ENTRY",
        verbose_name="ID ENTRY",
    )