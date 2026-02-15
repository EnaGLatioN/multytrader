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
from exchange.models import WalletPair, Exchange
import subprocess
from .forms import EntryForm
from trade.bot import notification
from decouple import config


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


class OrderAdmin(ModelAdmin):
    fields = ('trade_type', 'entry', 'exchange_account', 'proxy')
    list_display = ('entry', 'trade_type', 'exchange_account', 'proxy', 'status')


class OrderInline(TabularInline):
    model = Order
    extra = 1
    fields = ('exchange_account', 'trade_type', 'proxy')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'exchange_account' and not request.user.is_superuser:
            kwargs["queryset"] = ExchangeAccount.objects.filter(user_exchange_account = request.user)
        if db_field.name == 'proxy':
            kwargs["queryset"] = Proxy.objects.filter(is_active = True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class DynamicOrderInline(TabularInline):
    """Инлайн для конкретной биржи"""
    model = Order
    fields = ['exchange_account', 'proxy', 'trade_type', 'status', 'ex_order_id']
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
        ("Основные настройки", {
            "fields": (
                'alias', 
                'profit', 
                'exit_course', 
                'entry_course', 
                'shoulder',
                'wallet_pair', 
                'exchanges'  # Поле выбора бирж
            )
        }),
        ("Дополнительно", {
            "fields": ("receive_notifications", "is_active", "reverse"),
            "classes": ("wide",),
        }),
    )
    list_display = (
        'alias',
        'profit', 
        'shoulder',
        'exit_course', 
        'entry_course',
        'wallet_pair', 
        'get_exchanges_display',
        'status'
    )
    list_filter = ('status',)
    
    class Media:
        js = (
            'admin/js/jquery.init.js',
            'js/admin_dynamic_fields.js',
            'admin/js/jazzmin_tabs_fix.js',
            'admin/js/dynamic_exchange_inlines.js',
        )
    
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
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # При загрузке формы проверяем, есть ли в сессии выбранные биржи
        if 'selected_exchanges' in request.session:
            # Можно передать в контекст для предзаполнения поля
            extra_context = extra_context or {}
            exchange_ids = request.session['selected_exchanges']
            extra_context['selected_exchanges'] = exchange_ids
        
        return super().changeform_view(request, object_id, form_url, extra_context)

    # Остальные методы без изменений
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'wallet_pair': 
            if request.user.is_superuser:
                kwargs["queryset"] = WalletPair.objects.filter(is_active=True)
            else:
                kwargs["queryset"] = WalletPair.objects.filter(
                    customuser_wallet_pairs=request.user, 
                    is_active=True
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset 
        return queryset.filter(order_entry__exchange_account__user_exchange_account=request.user).distinct()
    
    def save_form(self, request, form, change):
        instance = super().save_form(request, form, change)
        new_is_active = form.cleaned_data['is_active']
        if change:
            entry = Entry.objects.get(id = instance.id)
            old_is_active = entry.is_active
            new_is_active = form.cleaned_data['is_active']
            old_receive_notifications = entry.chat_id
            new_receive_notifications = form.cleaned_data.get('receive_notifications', False)
            
            if old_is_active and not new_is_active: #  изменили статус на не актив
                self._delete_process(request, form.instance) # тушим процесс
                instance.status = EntryStatusType.STOPPED # поменяли на стутс STOPPED
        
            elif new_is_active and not old_is_active: #  изменили статус на актив
                self._create_process(str(form.instance.id)) # создаем процесс
                instance.status = EntryStatusType.WAIT # поменяли на стутс WAIT
            
            if old_receive_notifications and not new_receive_notifications: #если были включены а щас нет
                instance.chat_id = None
            elif new_receive_notifications and not old_receive_notifications: #если были выключены а щас включены
                instance.chat_id = request.user.chat_id
        else:
            if not new_is_active:
                instance.status = EntryStatusType.STOPPED # поменяли на стутс STOPPED

            receive_notifications = form.cleaned_data.get('receive_notifications', False)
            if receive_notifications:
                if chat_id := request.user.chat_id:
                    instance.chat_id = chat_id
                else:
                    warning(request, f"Добавьте чат айди в разделе 'Пользователи', чтобы получать уведомления в Telegram")
        return instance
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not change and form.instance.is_active:
            self._create_process(str(form.instance.id))
    
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
    
    def _create_process(self, entry_id):
        if Process.objects.filter(entry_id=entry_id).exists():
            log.warning(f"Процесс для входа {entry_id} уже существует")
            return

        with open("process.log", "a") as log_file:
            active_process = subprocess.Popen(
                ["poetry", "run", "python", config("MANAGE_DIR", cast=str, default="manage.py"), "start_entry", # poetry run python -m manage start_entry --entry_id
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


admin.site.register(Entry, EntryAdmin)
admin.site.register(Order, OrderAdmin)
