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
    BigIntegerField,
    BooleanField
)
from trader.models import ExchangeAccount, Proxy
from exchange.models import WalletPair


class OrderStatusType(TextChoices):
    WAIT = "WAIT", "В Ожидании"
    OPEN = "OPEN", "Открыт"
    CLOSED = "CLOSED", "Закрыт"
    FAILED = "FAILED", "Завершен с ошибкой"


class EntryStatusType(TextChoices):
    WAIT = "WAIT", "В Ожидании"
    ACTIVE = "ACTIVE", "Активно"
    COMPLETED = "COMPLETED", "Завершено"
    STOPPED = "STOPPED", "Остановлен"
    FAILED = "FAILED", "Завершен с ошибкой"


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
    alias = CharField(
        blank = True,
        null = True,
        max_length = 50,
        help_text="Добавьте псевдоним входа для вашего удобства",
        verbose_name="Псевдоним"
    )
    profit = FloatField(
        blank = True,
        null = True,
        help_text="Колличество контрактов",
        verbose_name="Колличество контрактов"
    )
    shoulder = PositiveIntegerField(
        help_text="Плечо",
        verbose_name="Плечо",
        blank = True
    )
    status = CharField(
        choices=EntryStatusType.choices,
        default=EntryStatusType.WAIT.value,
        max_length = 50,
        help_text="Статус",
        verbose_name="Статус",
    )
    exit_course = FloatField(
        blank=True,
        null=True,
        help_text="Курс выхода",
        verbose_name="Курс выхода"
    )
    entry_course = FloatField(
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
    chat_id = BigIntegerField(
        verbose_name="Чат айди в тг",
        help_text="Введите чат айди в тг если хотите получать уведомления об этом входе",
        blank=True,
        null=True,
    )
    is_active = BooleanField(
        default=True,
        help_text="Активен ли вход",
        verbose_name="Активность"
    )
    reverse = BooleanField(
        default=True,
        help_text="Реверс",
        verbose_name="Реверс",
        db_default=False
    )
    class Meta:
        db_table = "entry"
        verbose_name = "Вход"
        verbose_name_plural = "Входы"
        ordering = ("-created_at",)

    def __str__(self):
        return f'{self.alias}' if self.alias else f'{self.id}'


class Order(Model):
    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор ",
        primary_key=True,
        verbose_name="ID",
    )
    trade_type = CharField(
        choices=TradeType.choices,
        max_length = 50,
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
        blank=True,
        null=True,
        on_delete=CASCADE,
        related_name="order_proxy",
        verbose_name="Прокси",
    )
    ex_order_id = CharField(
        max_length = 255,
        help_text="Айди ордера с биржи.",
        verbose_name="Айди ордера с биржи.",
        blank=True,
        null=True,
        default=None
    )
    status = CharField(
        choices=OrderStatusType.choices,
        default=OrderStatusType.WAIT.value,
        max_length = 50,
        help_text="Статус",
        verbose_name="Статус",
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
        max_length=255,
        help_text="ID ENTRY",
        verbose_name="ID ENTRY",
    )