from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exchange', '0013_exchange_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='pairexchangemapping',
            name='step',
            field=models.FloatField(default=0, help_text='Минимальный шаг изменения ордера (в монетах)', verbose_name='Шаг'),
        ),
    ]
