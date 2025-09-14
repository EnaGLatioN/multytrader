from django.urls import path
from . import views

app_name = 'trade'

urlpatterns = [
    path('', views.get_exchange_accounts, name='get_exchange_accounts'),
]