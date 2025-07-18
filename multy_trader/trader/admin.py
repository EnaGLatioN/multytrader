from django.contrib.admin import AdminSite
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.contrib.auth import get_user_model


class TradeAdminSite(AdminSite):
    site_header = "MultyTrade Admin"
    site_title = "Администрирование"
    index_title = "Добро пожаловать в админку"


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'fields': ('walet_pairs_gate', 'walet_pairs_mexc'),  # Исправлено на правильные поля
        }),
    )
    fieldsets = UserAdmin.fieldsets + (
        (None, {
            'fields': ('walet_pairs_gate', 'walet_pairs_mexc'),  # Исправлено на правильные поля
        }),
    )

User = get_user_model()

my_admin_site = TradeAdminSite(name='myadmin')

my_admin_site.register(CustomUser, CustomUserAdmin)
my_admin_site.register(Group)