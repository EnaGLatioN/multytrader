from django.contrib import admin
from .models import OrderBook
from trader.admin import my_admin_site


class OrderBookAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'current_bid', 'current_ask', 'spread', 'timestamp')
    ordering = ('-timestamp',)
    search_fields = ('symbol',)

my_admin_site.register(OrderBook, OrderBookAdmin)