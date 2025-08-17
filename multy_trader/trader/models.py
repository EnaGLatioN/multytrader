from uuid import uuid4
from encrypted_model_fields.fields import EncryptedCharField
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    Model,
    CASCADE,
    ManyToManyField,
    CharField,
    PositiveIntegerField,
    UUIDField,
    GenericIPAddressField,
    BooleanField,
    DateTimeField,
    UniqueConstraint,
    ForeignKey
)
from exchange.models import Exchange, WalletPair


class Proxy(Model):
    """
    Модель для хранения конфигурации прокси-серверов, 
    используемых для подключения к биржевым API.
    """

    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор",
        primary_key=True,
        verbose_name="ID",
    )
    ip_address = GenericIPAddressField(
        help_text="IP адрес прокси-сервера",
        verbose_name="IP адрес",
        protocol="both"
    )
    port = PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(65535)], 
        help_text="Порт для подключения к прокси",
        verbose_name="Порт"
    )
    login = CharField(
        help_text="Логин для аутентификации",
        verbose_name="Логин",
        max_length=128
    )
    password = EncryptedCharField(
        help_text="Пароль для аутентификации",
        verbose_name="Пароль",
        max_length=250
    )
    is_active = BooleanField(
        default=True,
        help_text="Активен ли прокси",
        verbose_name="Активность"
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text="Дата создания",
        verbose_name="Дата создания",
    )
    
    class Meta:
        db_table = "proxy"
        verbose_name = "Прокси"
        verbose_name_plural = "Прокси"
        ordering = ["-created_at"]
        constraints = [
            UniqueConstraint(fields=['ip_address', 'port', 'login', 'password'], name='unique_data_proxy')
        ]

    def __str__(self):
        return f"{self.ip_address}:{self.port}"


class ExchangeAccount(Model):
    """
    Модель для хранения данных аккаунта на криптобирже.
    """

    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор",
        primary_key=True,
        verbose_name="ID",
    )
    api_key = EncryptedCharField(
        help_text="API ключ",
        verbose_name="API ключ",
    )
    secret_key = EncryptedCharField(
        help_text="Секретный ключ",
        verbose_name="Секретный ключ",
    )
    login = CharField(
        help_text="Логин для аутентификации",
        verbose_name="Логин",
        max_length=128
    )
    password = EncryptedCharField(
        help_text="Пароль для аутентификации",
        verbose_name="Пароль",
        max_length=250
    )
    is_active = BooleanField(
        default=True,
        help_text="Активен ли аккаунт",
        verbose_name="Активность"
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text="Дата создания",
        verbose_name="Дата создания",
    )
    proxies = ManyToManyField(
        Proxy,
        related_name="exchange_account_proxy",
        verbose_name="Прокси",
    )
    exchange = ForeignKey(
        Exchange,
        on_delete=CASCADE,
        related_name="exchange_account_exchange",
        verbose_name="Биржа",
    )

    class Meta:
        db_table = "exchange_account"
        verbose_name = "Биржевый аккаунт"
        verbose_name_plural = "Биржевые аккаунты"
        ordering = ["login"]

    def __str__(self):
        return f'{self.login} {self.exchange}'
    

class CustomUser(AbstractUser):
    wallet_pairs = ManyToManyField(
        WalletPair,
        related_name='customuser_wallet_pairs',
        verbose_name='Валютные пары',
        blank=True,
        null=True,
    )
    groups = ManyToManyField(
        Group,
        related_name='customuser_groups',
        verbose_name='Группы',
        blank=True,
    )
    user_permissions = ManyToManyField(
        Permission,
        related_name='customuser_permissions',
        verbose_name='Разрешения',
        blank=True,
    )
    exchange_account = ManyToManyField(
        ExchangeAccount,
        related_name="user_exchange_account",
        verbose_name="Биржевый аккаунт",
        blank=True,
        null=True,
    )
    maximum_amount = PositiveIntegerField(
        verbose_name="Максимальная сумма",
        help_text="Максимальная сумма в рублях",
        blank=True,
        null = True,
    )
