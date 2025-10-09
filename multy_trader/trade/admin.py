import os
import signal
import logging
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Entry, Order, Process
from trader.admin import my_admin_site
from trader.models import ExchangeAccount, Proxy
from exchange.models import WalletPair, Exchange
import subprocess
from .forms import EntryForm
from trade.bot import notification


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class OrderInline(TabularInline):
    model = Order
    extra = 1
    max_num = 1
    fields = ('exchange_account', 'trade_type', 'proxy')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'exchange_account' and not request.user.is_superuser:
            kwargs["queryset"] = ExchangeAccount.objects.filter(user_exchange_account = request.user)
        if db_field.name == 'proxy':
            kwargs["queryset"] = Proxy.objects.filter(is_active = True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class EntryAdmin(ModelAdmin):
    form = EntryForm
    fields = ('profit', 'exit_course', 'entry_course', 'shoulder', 'exchange_one', 'exchange_two','wallet_pair', 'chat_id')
    list_display = ('profit', 'shoulder','exit_course', 'entry_course','wallet_pair', 'status')
    list_filter = ('status',)
    inlines = [OrderInline, OrderInline]
    
    class Media:
        js = (
            'admin/js/jquery.init.js',
            'js/admin_dynamic_fields.js',
        )

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
            entry_id = str(form.instance.id)
            with open("process.log", "a") as log_file:
                active_process = subprocess.Popen(
                    ["poetry", "run", "python", "-m", "manage", "start_entry",
                     "--entry_id", entry_id,
                     ],
                    stdout=log_file,
                    stderr=log_file,
                    text=True
                )
                Process.objects.create(
                    pid=active_process.pid,
                    entry_id=entry_id
                )

    def delete_model(self, request, obj):
        self._delete_process(request, obj)
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self._delete_process(request, obj)
        super().delete_queryset(request, queryset)

    def _delete_process(self, request, obj):
        entry_id = obj.id
        try:
            process = Process.objects.get(entry_id=str(entry_id))
            os.kill(process.pid, signal.SIGTERM)
            process.delete()
        except Process.DoesNotExist:
            log.warning(f"Не найден процесс для входа {entry_id}")
        except Exception as e:
            log.error(f"delete_model -- trade -- {e}")

my_admin_site.register(Entry, EntryAdmin)
