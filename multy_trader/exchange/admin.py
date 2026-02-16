from django.contrib.admin import ModelAdmin, TabularInline
from .models import Exchange, WalletPair, PairExchangeMapping
from django.contrib import admin
from .forms import WalletPairAdminForm


class ExchangeAdmin(ModelAdmin):
    search_fields = ('name',)
    search_help_text = 'Введите название биржи для поиска'
    fieldsets = (
        ("Основная информация", {
            "fields": ("name",)
            }
        ),
        ("Системная информация", {
            "fields": ("base_url", "api_endpoint", "max_limit", "min_limit"),
            "description": "Данные необходимые для покупки"
            }
        ),
    )


class PairExchangeInline(TabularInline):
    model = PairExchangeMapping
    fields = ('local_name', 'exchange')


class WalletPairAdmin(ModelAdmin):
    form = WalletPairAdminForm
    search_fields = ('slug',)
    list_display = ('slug', 'is_active', 'get_pairs')
    list_filter = ('is_active',)
    search_help_text = 'Введите валютную пару для поиска'
    
    fieldsets = (
        ("Основная информация", {
            "fields": ('slug', 'is_active')
        }),
        ("Связанные валютные пары", {
            "fields": ("selected_pairs",),
            "description": "Выберите существующие пары из списка",
            "classes": ("wide",),
        }),
    )

    def get_pairs(self, obj):
        pairs = obj.exchange_mappings.all()
        return ", ".join([p.local_name for p in pairs]) or "Нет пар"
    
    get_pairs.short_description = "Валютные пары бирж"

    def save_model(self, request, obj, form, change):
        """Сохраняет объект и обновляет связи"""
        obj.save()
        
        if 'selected_pairs' in form.cleaned_data:
            selected_pairs = form.cleaned_data['selected_pairs']
            PairExchangeMapping.objects.filter(wallet_pair=obj).update(wallet_pair=None)
            selected_ids = [p.id for p in selected_pairs]
            PairExchangeMapping.objects.filter(id__in=selected_ids).update(wallet_pair=obj)

admin.site.register(Exchange, ExchangeAdmin)
admin.site.register(WalletPair, WalletPairAdmin)
