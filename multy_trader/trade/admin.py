import os
import errno
import signal
import logging
from email.policy import default

from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.messages import warning
from .models import Entry, Order, Process, EntryStatusType
from django.contrib import admin
from trader.models import ExchangeAccount, Proxy
from exchange.models import WalletPair, Exchange, PairExchangeMapping
import subprocess
from .forms import EntryForm
from decouple import config
from django.db.models import Count


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


class OrderInline(TabularInline):
    model = Order
    extra = 0
    fields = ('exchange_account', 'proxy', 'trade_type', 'id')
    readonly_fields = ('id',)
    verbose_name = "Все ордера входа"
    verbose_name_plural = "Список всех ордеров"

class DynamicOrderInline(TabularInline):
    """Инлайн для конкретной биржи"""
    model = Order
    fields = ['exchange_account', 'proxy', 'trade_type']
    extra = 1
    can_delete = True
    template = 'admin/edit_inline/tabular.html'
    
    def __init__(self, parent_model, admin_site, exchange=None):
        super().__init__(parent_model, admin_site)
        self.exchange = exchange
        if exchange:
            self.verbose_name = f"Ордера для {exchange.name}"
            self.verbose_name_plural = f"Ордера для {exchange.name}"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.exchange:
            return qs.filter(exchange_account__exchange=self.exchange)
        return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "exchange_account" and self.exchange:
            kwargs["queryset"] = ExchangeAccount.objects.filter(
                exchange=self.exchange,
                is_active=True
            )
        elif db_field.name == 'proxy':
            kwargs["queryset"] = Proxy.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def has_add_permission(self, request, obj=None):
        return bool(self.exchange)
    
    def has_change_permission(self, request, obj=None):
        return bool(self.exchange)


class EntryAdmin(ModelAdmin):
    form = EntryForm
    fieldsets = (
        ("Биржи", {
            "fields": (
                'exchanges',
            )
        }),
        ("Основные настройки", {
            "fields": (
                'alias',
                'wallet_pair',
                'profit', 
                'exit_course', 
                'entry_course', 
                'shoulder'
            )
        }),
        ("Дополнительно", {
            "fields": ("receive_notifications", "is_active", "reverse", "restart"),
            "classes": ("wide",),
        }),
    )
    list_display = (
        'alias',
        'trader',
        'profit', 
        'shoulder',
        'exit_course', 
        'entry_course',
        'wallet_pair', 
        'get_exchanges_display',
        'status'
    )
    list_filter = ('status','trader')
    actions = ['action_closed']
    
    class Media:
        js = (
            'admin/js/jquery.init.js',
            'admin/js/dynamic_exchange_inlines.js',
            'admin/js/min_order_hint.js'
        )

    @admin.action(description="Закрыть позицию")
    def action_closed(self, request, queryset):
        for entry in queryset:
            self._delete_process(request, entry)
        queryset.update(status='STOPPED', is_active=False)

    def get_exchanges_display(self, obj):
        """Отображаем выбранные биржи"""
        if obj.pk:
            # Получаем уникальные биржи из ордеров
            exchange_names = Order.objects.filter(
                entry=obj
            ).values_list(
                'exchange_account__exchange__name', flat=True
            ).distinct()
            return ", ".join(exchange_names) if exchange_names else "Не выбраны"
        return "Не выбраны"
    get_exchanges_display.short_description = "Биржи"

    def get_inlines(self, request, obj):
        inlines = []
        if obj:
            return [OrderInline]

        exchange_ids = request.session.get('selected_exchanges', [])
        
        if exchange_ids:
            exchanges = Exchange.objects.filter(id__in=exchange_ids)
            for exchange in exchanges:
                def create_inline_class(exch):
                    return type(
                        f'DynamicOrderInlineFor{exch.id}',
                        (DynamicOrderInline,),
                        {
                            '__init__': lambda self, parent_model, admin_site: 
                                DynamicOrderInline.__init__(self, parent_model, admin_site, exch),
                        }
                    )
                inline_class = create_inline_class(exchange)
                inlines.append(inline_class)
       
        return inlines
        
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.method == 'GET':
            exchange_ids = []
            if obj:
                exchange_ids = list(Order.objects.filter(entry=obj)
                    .values_list('exchange_account__exchange_id', flat=True)
                    .distinct())
            
            if not exchange_ids:
                exchange_ids = request.session.get('selected_exchanges', [])

            if 'exchanges' in form.base_fields:
                form.base_fields['exchanges'].initial = Exchange.objects.filter(id__in=exchange_ids)
        
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'wallet_pair':
            exchange_ids = request.session.get('selected_exchanges', [])
            if exchange_ids:
                id_wallet = PairExchangeMapping.objects.filter(
                    exchange_id__in=exchange_ids
                ).values('normalized_name').annotate(
                    exchange_count=Count('exchange_id', distinct=True)
                ).filter(
                    exchange_count=len(exchange_ids)
                ).values_list('wallet_pair', flat=True)
                
                if request.user.is_superuser:
                    kwargs["queryset"] = WalletPair.objects.filter(
                        is_active=True,
                        id__in=id_wallet
                    )
                else:
                    kwargs["queryset"] = WalletPair.objects.filter(
                        customuser_wallet_pairs=request.user, 
                        is_active=True,
                        id__in=id_wallet
                    )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset 
        return queryset.filter(order_entry__exchange_account__user_exchange_account=request.user).distinct()
    
    def save_form(self, request, form, change):
        form.cleaned_data.pop('exchanges', None)
        instance = super().save_form(request, form, change)
        new_is_active = form.cleaned_data['is_active']
        if change:
            entry = Entry.objects.get(id = instance.id)
            old_is_active = entry.is_active
            new_is_active = form.cleaned_data['is_active']
            
            if old_is_active:
                if not new_is_active: #  изменили статус на не актив
                    self._delete_process(request, form.instance) # тушим процесс
                    instance.status = EntryStatusType.STOPPED # поменяли на стутс STOPPED !!!
                else:
                    self._update_process(request, form.instance)
            elif new_is_active and not old_is_active: #  изменили статус на актив
                instance.status = EntryStatusType.WAIT # поменяли на стутс WAIT
                self._create_process(str(form.instance.id), form.instance.restart) # создаем процесс
            
        else:
            if not new_is_active:
                instance.status = EntryStatusType.STOPPED # поменяли на стутс STOPPED
        return instance
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not change and form.instance.is_active:
            self._create_process(str(form.instance.id), form.instance.restart)
    
    def save_model(self, request, obj, form, change):
        if not change: 
            obj.trader = request.user
            request.session['selected_exchanges'] = []
        super().save_model(request, obj, form, change)
    
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
        except OSError as e:
            if e.errno == errno.ESRCH:
                log.warning(f"Процесс с PID {process.pid} для входа {entry_id} уже не существует")
                process.delete()
            else:
                log.error(f"Неизвестная ошибка OSError: {e}")
        except Exception as e:
            log.error(f"delete_model -- trade -- {e}")

    def _update_process(self, request, obj):
        entry_id = obj.id
        try:
            process = Process.objects.get(entry_id=str(entry_id))
            os.kill(process.pid, signal.SIGUSR1)
        except Process.DoesNotExist:
            log.warning(f"Не найден процесс для входа {entry_id}")
        except Exception as e:
            log.error(f"update-model -- trade -- {e}")

    def _create_process(self, entry_id, restart):
        if Process.objects.filter(entry_id=entry_id).exists():
            log.warning(f"Процесс для входа {entry_id} уже существует")
            return

        command = ["poetry", "run", "python", config("MANAGE_DIR", cast=str, default="manage.py"), "dealer", # poetry run python -m manage start_entry --entry_id
            "--entry_id", entry_id
        ]
        if restart:
            command.append("--restart")
            
        with open("process.log", "a") as log_file:
            active_process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=log_file,
                text=True
            )
            Process.objects.create(
                pid=active_process.pid,
                entry_id=entry_id
            )


admin.site.register(Entry, EntryAdmin)
