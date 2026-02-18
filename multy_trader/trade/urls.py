from django.urls import path
from . import views

app_name = 'trade'

urlpatterns = [
    path('', views.get_exchange_accounts, name='get_exchange_accounts'),
    path('save-exchanges-to-session/', views.save_exchanges_to_session, name='save_exchanges_to_session'),
    path('clear-exchanges-session/', views.clear_exchanges_session, name='clear_exchanges_session'),
    path('get-min-order/', views.get_min_order, name='get_min_order'),
]
