from django.apps import AppConfig


class TradeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trade'
    verbose_name = 'Торговля'

    def ready(self):
        import trade.signals
