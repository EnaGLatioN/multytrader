from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Proxy, ExchangeAccount
from django.contrib.auth import get_user_model


class TradeAdminSite(AdminSite):
    site_header = "MultyTrade Admin"
    site_title = "Администрирование"
    index_title = "Добро пожаловать в админку"


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'fields': ('exchange_account', 'wallet_pairs', 'maximum_amount'),
        }),
    )
    fieldsets = UserAdmin.fieldsets + (
         ('Дополнительная информация', {
             'fields': ('exchange_account', 'wallet_pairs', 'maximum_amount'),
         }),
    )
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'exchange_account':
            kwargs["widget"] = FilteredSelectMultiple('Биржевые аккаунты', is_stacked=False)
        if db_field.name == 'wallet_pairs':
            kwargs["widget"] = FilteredSelectMultiple('Валютные пары', is_stacked=False)

        return super().formfield_for_manytomany(db_field, request, **kwargs)

class CustomProxy(ModelAdmin):
    fields = ('ip_address', 'port', 'login', 'password', 'is_active')
    list_display = ('ip_address', 'port', 'is_active')
    search_fields = ('ip_address',)
    search_help_text = 'Введите IP-адрес для поиска'


class CustomExchangeAccount(ModelAdmin):
    fields = ('login', 'password', 'api_key', 'secret_key','exchange', 'proxies', 'is_active')
    list_display = ('login', 'is_active')
    search_fields = ('login',)
    search_help_text = 'Введите логин'
    list_filter = ('is_active', 'exchange')
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'proxies':
            kwargs["queryset"] = Proxy.objects.filter(is_active=True)
            kwargs["widget"] = FilteredSelectMultiple('Прокси', is_stacked=False)

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self,request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user_exchange_account = request.user)
        return qs
    
    def save_model(self,request,obj,form,change):
        super().save_model(request,obj,form,change)
        if not change and not request.user.is_superuser:
            obj.user_exchange_account.add(request.user)
        
User = get_user_model()

my_admin_site = TradeAdminSite(name='myadmin')

my_admin_site.register(CustomUser, CustomUserAdmin)
my_admin_site.register(Proxy, CustomProxy)
my_admin_site.register(ExchangeAccount, CustomExchangeAccount)
my_admin_site.register(Group)