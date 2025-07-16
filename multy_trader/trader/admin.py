from django.contrib.admin import AdminSite
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from gate.models import CustomUser, WaletPairs
from django.contrib.auth import get_user_model


class TradeAdminSite(AdminSite):
    site_header = "MultyTrade Admin"
    site_title = "Администрирование"
    index_title = "Добро пожаловать в админку"


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'fields': ('walet_pairs',)
        }),
    )
    fieldsets = UserAdmin.fieldsets + (
        (None, {
            'fields': ('walet_pairs',)
        }),
    )


User = get_user_model()
admin.site.unregister(User)

my_admin_site = TradeAdminSite(name='myadmin')
my_admin_site.register(CustomUser, CustomUserAdmin)
my_admin_site.register(WaletPairs)
my_admin_site.register(Group)