from django.contrib.admin import ModelAdmin
from .models import Exchange, WalletPair, PairExchangeMapping
from trader.admin import my_admin_site


class ExchangeAdmin(ModelAdmin):
    fields = ('name', 'base_url', 'api_endpoint','max_limit', 'min_limit')
    search_fields = ('name',)
    search_help_text = 'Введите название биржи для поиска'


class PairExchangeMappingAdmin(ModelAdmin):
    fields = ('local_name', 'coin_count', 'min_order', 'wallet_pair', 'exchange')
    search_fields = ('local_name',)
    list_display = ('local_name', 'wallet_pair', 'exchange')
    list_filter = ('exchange',)
    search_help_text = 'Введите название валютной пары для поиска'


class WalletPairAdmin(ModelAdmin):
    fields = ('slug', 'is_active',)
    search_fields = ('slug',)
    list_display = ('slug', 'is_active', 'get_pairs')
    list_filter = ('is_active',)
    search_help_text = 'Введите валютную пару для поиска'

    def get_pairs(self,obj):
        pairs = obj.exchange_mappings.all()
        normalized_pairs = [pair.local_name for pair in pairs]
        return ", ".join(normalized_pairs) or "Нет пар"

    get_pairs.short_description = "Валютные пары бирж"


my_admin_site.register(Exchange, ExchangeAdmin)
my_admin_site.register(WalletPair, WalletPairAdmin)
my_admin_site.register(PairExchangeMapping, PairExchangeMappingAdmin)
