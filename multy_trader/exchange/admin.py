from django.contrib.admin import ModelAdmin
from .models import Exchange, WalletPair
from trader.admin import my_admin_site


class ExchangeAdmin(ModelAdmin):
    fields = ('name', 'wallet_pairs')
    search_fields = ('name',)
    search_help_text = 'Введите название биржи для поиска'

class WalletPairAdmin(ModelAdmin):
    fields = ('slug',)
    search_fields = ('slug',)
    search_help_text = 'Введите валютную пару для поиска'

my_admin_site.register(Exchange, ExchangeAdmin)
my_admin_site.register(WalletPair, WalletPairAdmin)

