from django.contrib import admin
from .models import WaletPairsMexc
from trader.admin import my_admin_site


#class PairsMexcAdmin(admin.ModelAdmin):
#    list_display = ('slug', 'created_at')
#    ordering = ('-created_at',)
#    search_fields = ('slug',)


#my_admin_site.register(WaletPairsMexc, PairsMexcAdmin)