from django.contrib.admin import AdminSite, ModelAdmin
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
            'fields': ('walet_pairs_gate', 'walet_pairs_mexc', 'exchange_account', 'maximum_amount'),
        }),
    )
    fieldsets = UserAdmin.fieldsets + (
        (None, {
            'fields': ('walet_pairs_gate', 'walet_pairs_mexc', 'exchange_account', 'maximum_amount'),
        }),
    )


class CustomProxy(ModelAdmin):
    fields = ('ip_address', 'port', 'login', 'password', 'is_active')
    list_display = ('ip_address', 'port', 'is_active')
    search_fields = ('ip_address',)
    search_help_text = 'Введите IP-адрес для поиска'


class CustomExchangeAccount(ModelAdmin):
    fields = ('login', 'password', 'proxies', 'is_active')
    list_display = ('login', 'is_active')
    search_fields = ('login',)
    search_help_text = 'Введите логин'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'proxies':
            kwargs["queryset"] = Proxy.objects.filter(is_active=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

User = get_user_model()

my_admin_site = TradeAdminSite(name='myadmin')

my_admin_site.register(CustomUser, CustomUserAdmin)
my_admin_site.register(Proxy, CustomProxy)
my_admin_site.register(ExchangeAccount, CustomExchangeAccount)
my_admin_site.register(Group)