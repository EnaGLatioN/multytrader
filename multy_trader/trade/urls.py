from django.urls import path
from . import views

app_name = 'trade'

urlpatterns = [
    path('', views.get_exchange_accounts, name='get_exchange_accounts'),
    path('save-exchanges-to-session/', views.save_exchanges_to_session, name='save_exchanges_to_session'),
    path('get-min-profit/', views.get_min_profit, name='get_min_profit'),
]
