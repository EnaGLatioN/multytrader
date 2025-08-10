from django.contrib import admin
from .models import OrderBook, WaletPairs
from trader.admin import my_admin_site


#class OrderBookAdmin(admin.ModelAdmin):
#    list_display = ('symbol', 'current_bid', 'current_ask', 'spread', 'timestamp')
#    ordering = ('-timestamp',)
#    search_fields = ('symbol',)


#class PairsGateAdmin(admin.ModelAdmin):
#    list_display = ('slug', 'created_at')
#    ordering = ('-created_at',)
#    search_fields = ('slug',)


#my_admin_site.register(OrderBook, OrderBookAdmin)
#my_admin_site.register(WaletPairs, PairsGateAdmin)