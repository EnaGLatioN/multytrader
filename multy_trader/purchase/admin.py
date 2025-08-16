from django.contrib.admin import ModelAdmin, TabularInline
from .models import Entry, Order
from trader.admin import my_admin_site
from trader.models import ExchangeAccount


class OrderInline(TabularInline):
    model = Order
    extra = 0
    fields = ('entry_course', 'trade_type', 'exchange_account')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'exchange_account' and not request.user.is_superuser:
            kwargs["queryset"] = ExchangeAccount.objects.filter(user_exchange_account = request.user)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class EntryAdmin(ModelAdmin):
    fields = ('exit_course', 'shoulder','count','is_active')
    list_display = ('profit', 'shoulder','count', 'exit_course', 'is_active')
    list_filter = ('is_active',)
    inlines = [OrderInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset 
        return queryset.filter(order_entry__exchange_account__user_exchange_account=request.user).distinct()


my_admin_site.register(Entry, EntryAdmin)
