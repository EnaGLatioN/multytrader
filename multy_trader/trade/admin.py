from django.contrib.admin import ModelAdmin, TabularInline
from .models import Entry, Order, TradeType
from trader.admin import my_admin_site
from trader.models import ExchangeAccount
from exchange.models import WalletPair
from .services.services import send_order_to_exchange_api


class OrderInline(TabularInline):
    model = Order
    extra = 0
    fields = ('entry_course', 'trade_type', 'exchange_account')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'exchange_account' and not request.user.is_superuser:
            kwargs["queryset"] = ExchangeAccount.objects.filter(user_exchange_account = request.user)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class EntryAdmin(ModelAdmin):
    fields = ('exit_course', 'shoulder','count','wallet_pair','is_active')
    list_display = ('profit', 'shoulder','count', 'exit_course', 'is_active')
    list_filter = ('is_active',)
    inlines = [OrderInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'wallet_pair': 
            if request.user.is_superuser:
                kwargs["queryset"] = WalletPair.objects.filter(
                    is_active = True
                )
            else:
                kwargs["queryset"] = WalletPair.objects.filter(
                    customuser_wallet_pairs = request.user, 
                    is_active = True
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset 
        return queryset.filter(order_entry__exchange_account__user_exchange_account=request.user).distinct()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        if not change:
            send_order_to_exchange_api(form.instance)

my_admin_site.register(Entry, EntryAdmin)