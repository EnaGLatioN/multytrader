from django.contrib.admin import ModelAdmin
from .models import Purchase
from trader.admin import my_admin_site


class PurchaseAdmin(ModelAdmin):
    fields = ('profit', 'entry_course', 'exit_course', 'is_active')
    list_display = ('profit', 'entry_course', 'exit_course', 'is_active')
    list_filter = ('is_active',)
    #search_fields = ('slug',)
    #search_help_text = 'Введите валютную пару для поиска'

my_admin_site.register(Purchase, PurchaseAdmin)

