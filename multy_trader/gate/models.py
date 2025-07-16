from django.db import models
from uuid import uuid4
from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    ForeignKey,
    Model,
    UUIDField,
    URLField,
    IntegerField,
    BooleanField,
    OneToOneField,
    TextField,
    BigIntegerField
)


class WaletPairs(models.Model):
    id = UUIDField(
        default=uuid4,
        help_text="Уникальный идентификатор публикации.",
        primary_key=True,
        verbose_name="ID публикации.",
    )
    slug = CharField(
        "Заголовок рубрики.",
        max_length=255,
        help_text="Заголовок рубрики",
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text="Дата создания",
        verbose_name="Дата создания",
    )
