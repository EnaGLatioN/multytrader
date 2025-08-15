from uuid import uuid4
from django.db.models import (
    Model,
    ManyToManyField,
    CharField,
    PositiveIntegerField,
    UUIDField,
    GenericIPAddressField,
    BooleanField,
    DateTimeField,
    UniqueConstraint
)
from django.core.validators import MaxValueValidator, MinValueValidator
from trader.models import CustomUser

class Purchase(Model):
    # можно добавить еще поле в котором будет хранится остаток маржи а маржу переименовать в исходную маржу
    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор ",
        primary_key=True,
        verbose_name="ID",
    )
    profit = PositiveIntegerField(
        validators=[MinValueValidator(1)], 
        help_text="Маржа",
        verbose_name="Маржа"
    )
    entry_course = PositiveIntegerField(
        help_text="Курс входа",
        verbose_name="Курс входа"
    )
    exit_course = PositiveIntegerField(
        help_text="Курс выхода",
        verbose_name="Курс выхода"
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
        db_table = "purchase"
        verbose_name = "Покупка/продажа"
        verbose_name_plural = "Покупка/продажа"
        ordering = ("-created_at",)

    def __str__(self):
        return f'{self.profit}'
