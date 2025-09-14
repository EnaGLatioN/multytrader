from django.contrib.admin import ModelAdmin
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import Exchange, WalletPair
from trader.admin import my_admin_site


class ExchangeAdmin(ModelAdmin):
    fields = ('name', 'base_url', 'api_endpoint','max_limit', 'min_limit')
    search_fields = ('name',)
    search_help_text = 'Введите название биржи для поиска'

class WalletPairAdmin(ModelAdmin):
    fields = ('slug', 'is_active', '')
    search_fields = ('slug',)
    list_display = ('slug','is_active',)
    list_filter = ('is_active',)
    search_help_text = 'Введите валютную пару для поиска'

my_admin_site.register(Exchange, ExchangeAdmin)
my_admin_site.register(WalletPair, WalletPairAdmin)
