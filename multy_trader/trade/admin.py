import os
import errno
import signal
import logging
import uuid
from email.policy import default

from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.messages import warning
from .models import Entry, Order, Process, EntryStatusType
from django.contrib import admin
from trader.models import ExchangeAccount, Proxy
from exchange.models import WalletPair, Exchange, PairExchangeMapping
import subprocess
from .forms import EntryForm
from trade.bot import notification
from decouple import config
from django.db.models import Count


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
    fields = ['exchange_account', 'proxy', 'trade_type']
    extra = 1
    can_delete = True
    template = 'admin/edit_inline/tabular.html'

    def __init__(self, parent_model, admin_site, exchange=None):
        super().__init__(parent_model, admin_site)
        self.exchange = exchange

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Если есть родительский объект (Entry), показываем его ордера для этой биржи
        if self.exchange and hasattr(self, 'parent_object') and self.parent_object:
            # ЯВНО фильтруем по entry и exchange
            return qs.filter(
                entry=self.parent_object,
                exchange_account__exchange=self.exchange
            )

        # Если нет родителя (новый объект), возвращаем пустой queryset
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "exchange_account" and self.exchange:
            # Показываем только аккаунты ЭТОЙ биржи
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

    def get_extra(self, request, obj=None, **kwargs):
        """Всегда показываем одну пустую форму для добавления"""
        return 1


class EntryAdmin(ModelAdmin):
    form = EntryForm
    fieldsets = (
        ("Биржи", {
            "fields": ('exchanges',)
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
            "fields": ("receive_notifications", "is_active", "reverse"),
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
    list_filter = ('status', 'trader')

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'admin/js/dynamic_exchange_inlines.js',
            'admin/js/min_order_hint.js'
        )

    def save_formset(self, request, form, formset, change):
        """Переопределяем для отладки сохранения формсетов"""
        log.info(f"Сохраняем формсет: {formset.prefix}")
        log.info(f"Формсет валиден: {formset.is_valid()}")

        if not formset.is_valid():
            log.error(f"Ошибки формсета {formset.prefix}: {formset.errors}")
            log.error(f"Ошибки формы: {[form.errors for form in formset.forms]}")

        super().save_formset(request, form, formset, change)


    def get_exchanges_display(self, obj):
        """Отображаем выбранные биржи"""
        if obj.pk:
            exchange_names = Order.objects.filter(
                entry=obj
            ).values_list(
                'exchange_account__exchange__name', flat=True
            ).distinct()
            return ", ".join(exchange_names) if exchange_names else "Не выбраны"
        return "Не выбраны"

    get_exchanges_display.short_description = "Биржи"

    # ========== ВАЖНО: МЕТОД get_inlines (был у тебя) ==========
    def get_inlines(self, request, obj):
        """Возвращает список классов инлайнов для выбранных бирж"""
        inlines = []
        exchange_ids = []

        # Определяем ID бирж
        if request.method == 'POST':
            if 'exchanges' in request.POST:
                raw_ids = request.POST.getlist('exchanges')
                try:
                    exchange_ids = [uuid.UUID(pid) for pid in raw_ids if pid]
                except (ValueError, TypeError):
                    exchange_ids = raw_ids
                log.info(f"POST: создаем инлайны для бирж {exchange_ids}")

        elif obj:
            exchange_ids = list(Order.objects.filter(
                entry=obj
            ).values_list(
                'exchange_account__exchange__id', flat=True
            ).distinct())
            log.info(f"GET: инлайны из ордеров {exchange_ids}")

        else:
            exchange_ids = request.session.get('selected_exchanges', [])
            log.info(f"NEW: инлайны из сессии {exchange_ids}")

        # Создаем инлайн для каждой биржи с ПРАВИЛЬНЫМ названием
        if exchange_ids:
            exchanges = Exchange.objects.filter(id__in=exchange_ids)
            for exchange in exchanges:
                def create_inline_class(exch):
                    # Создаем класс с нормальным verbose_name
                    attrs = {
                        '__init__': lambda self, parent_model, admin_site:
                        DynamicOrderInline.__init__(self, parent_model, admin_site, exch),
                        'verbose_name': exch.name,  # Просто название биржи
                        'verbose_name_plural': exch.name,  # И здесь тоже
                    }
                    return type(
                        f'DynamicOrderInlineFor{exch.id}',
                        (DynamicOrderInline,),
                        attrs
                    )

                inline_class = create_inline_class(exchange)
                inlines.append(inline_class)

        return inlines

    # ========== НОВЫЙ МЕТОД: get_inline_instances ==========
    def get_inline_instances(self, request, obj=None):
        """Создает экземпляры инлайнов и переименовывает их"""
        inline_instances = []

        for inline_class in self.get_inlines(request, obj):
            inline_instance = inline_class(self.model, self.admin_site)
            inline_instance.parent_object = obj

            # Жестко переименовываем инлайн
            if hasattr(inline_instance, 'exchange') and inline_instance.exchange:
                # Убираем "Ордера для" если оно там есть
                name = inline_instance.exchange.name
                inline_instance.verbose_name = name
                inline_instance.verbose_name_plural = name

                log.info(f"Переименовал инлайн в: {name}")

            if obj:
                qs = inline_instance.get_queryset(request)
                log.info(f"Инлайн {inline_instance.verbose_name}: загружено {qs.count()} ордеров")

            inline_instances.append(inline_instance)

        return inline_instances

    # ========== МЕТОД changeform_view ==========
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Обрабатываем просмотр формы с проверкой сохранения"""

        if request.method == 'POST':
            if 'exchanges' in request.POST:
                selected = request.POST.getlist('exchanges')
                log.info(f"POST: выбраны биржи {selected}")
                request.session['selected_exchanges'] = selected

        # Получаем ответ от родительского метода
        response = super().changeform_view(request, object_id, form_url, extra_context)

        # Проверяем, было ли сохранение успешным
        if request.method == 'POST' and hasattr(response, 'status_code'):
            if response.status_code == 302:  # Редирект после успешного сохранения
                log.info("✅ УСПЕХ: данные сохранены, редирект на список")
            elif response.status_code == 200:  # Страница с формой (возможно ошибки)
                log.info("❌ НЕУДАЧА: форма показана снова, есть ошибки")

                # Ищем ошибки в контексте
                if hasattr(response, 'context_data'):
                    if 'adminform' in response.context_data:
                        form = response.context_data['adminform'].form
                        if form.errors:
                            log.error(f"Ошибки формы: {form.errors}")

        return response

    # ========== ОСТАЛЬНЫЕ МЕТОДЫ (без изменений) ==========
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
        instance = super().save_form(request, form, change)
        new_is_active = form.cleaned_data['is_active']
        if change:
            entry = Entry.objects.get(id=instance.id)
            old_is_active = entry.is_active

            if old_is_active and not new_is_active:
                self._delete_process(request, form.instance)
                instance.status = EntryStatusType.STOPPED
            elif new_is_active and not old_is_active:
                self._create_process(str(form.instance.id))
                instance.status = EntryStatusType.WAIT
        else:
            if not new_is_active:
                instance.status = EntryStatusType.STOPPED
        return instance

    def save_related(self, request, form, formsets, change):
        """Сохраняем связанные объекты с принудительной валидацией"""
        log.info(f"save_related: сохраняем {len(formsets)} формсетов")

        # Принудительно валидируем и сохраняем каждый формсет
        for formset in formsets:
            log.info(f"Формсет {formset.prefix}:")
            log.info(f"  - данных: {len(formset.data)}")
            log.info(f"  - валиден: {formset.is_valid()}")

            if formset.is_valid():
                # Сохраняем формсет вручную
                instances = formset.save(commit=False)
                for obj in instances:
                    obj.entry = form.instance
                    obj.save()
                log.info(f"  - сохранено {len(instances)} объектов")

                # Удаляем помеченные на удаление
                for obj in formset.deleted_objects:
                    obj.delete()
                    log.info(f"  - удален объект {obj.id}")
            else:
                log.error(f"  - ОШИБКИ: {formset.errors}")

        # Вызываем родительский метод для гарантии
        super().save_related(request, form, formsets, change)

        # Запускаем процесс если нужно
        if not change and form.instance.is_active:
            self._create_process(str(form.instance.id))

    def save_model(self, request, obj, form, change):
        if not change:
            obj.trader = request.user
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

    def _create_process(self, entry_id):
        if Process.objects.filter(entry_id=entry_id).exists():
            log.warning(f"Процесс для входа {entry_id} уже существует")
            return

        with open("process.log", "a") as log_file:
            active_process = subprocess.Popen(
                ["poetry", "run", "python", config("MANAGE_DIR", cast=str, default="manage.py"), "dealer",
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
