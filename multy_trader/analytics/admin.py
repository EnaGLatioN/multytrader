from django.contrib import admin
from .models import Analytics


class AnalyticsAdmin(admin.ModelAdmin):
    #search_fields = ('name',)
    list_display = (
        "trader", 
        "wallet_pair",
        "entry",
        "get_exchange_long",
        "get_exchange_short",
        "profit", 
        'shoulder', 
        'target_entry_spread',
        'actual_entry_spread',
        'target_exit_spread',
        'actual_exit_spread',
        'pnl_percent',
        'pnl_currency',
        'created_at'
        )
    #search_help_text = 'Введите название биржи для поиска'
    fieldsets = (
        ("Основная информация", {
            "fields": (
                "trader", 
                "entry",
                "wallet_pair", 
                "profit", 
                'shoulder', 
                'exchange_long', 
                'exchange_short',
                'target_entry_spread',
                'actual_entry_spread',
                'target_exit_spread',
                'actual_exit_spread',
                'pnl_percent',
                'pnl_currency',
                'created_at',
                'start_time',
                'exit_time'
                )
            }
        ),
    )
    list_filter = ('status','trader','wallet_pair', 'exchange_long', 'exchange_short')
    readonly_fields = (
        'trader',
        'wallet_pair', 
        'profit', 
        'shoulder', 
        'exchange_long', 
        'exchange_short',
        'target_entry_spread',
        'actual_entry_spread',
        'target_exit_spread',
        'actual_exit_spread',
        'pnl_percent',
        'pnl_currency',
        'created_at',
        "entry",
        'start_time',
        'exit_time'

    )
    @admin.display(description='Биржи Лонг')
    def get_exchange_long(self, obj):
        return ", ".join([e.name for e in obj.exchange_long.all()])

    @admin.display(description='Биржи Шорт')
    def get_exchange_short(self, obj):
        return ", ".join([e.name for e in obj.exchange_short.all()])

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('exchange_long', 'exchange_short')

admin.site.register(Analytics, AnalyticsAdmin)