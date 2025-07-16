from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class TradeAdminSite(AdminSite):
    site_header = "MultyTrade Admin"
    site_title = "Администрирование"
    index_title = "Добро пожаловать в админку"

class UserAdmin(BaseUserAdmin):
    # Укажите, какие поля отображать
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}
         ),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('username',)

# Аннулируем регистрация модели пользователя, если она уже зарегистрирована
admin.site.unregister(User)

# Регистрация модели User в вашей кастомной админке
my_admin_site = TradeAdminSite(name='myadmin')
my_admin_site.register(User, UserAdmin)
my_admin_site.register(Group)  # Если хотите также управлять группами