import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from exchange.models import Exchange, WalletPair, PairExchangeMapping
from trader.models import ExchangeAccount
from trade.models import Order
from django.template.loader import render_to_string


@staff_member_required
@csrf_exempt
def get_exchange_accounts(request):
    """Возвращает аккаунты для выбранных бирж"""
    exchange_ids = request.GET.getlist('exchange_ids[]')
    if not exchange_ids:
        return JsonResponse({'accounts': []})
    
    accounts = ExchangeAccount.objects.filter(
        exchange_id__in=exchange_ids,
        is_active=True
    ).values('id', 'login', 'exchange__name')
    
    return JsonResponse({'accounts': list(accounts)})

 
@csrf_exempt
def save_exchanges_to_session(request):
    """Сохраняет выбранные биржи в сессию"""
    if request.method == 'POST':
        data = json.loads(request.body)
        exchange_ids = data.get('exchange_ids', [])
        entry_id = data.get('entry_id')
        
        request.session['selected_exchanges'] = exchange_ids
        request.session['entry_id'] = entry_id
        
        return JsonResponse({'status': 'ok'})

@csrf_exempt
def clear_exchanges_session(request):
    if request.method == 'POST':
        if 'selected_exchanges' in request.session:
            del request.session['selected_exchanges']
        return JsonResponse({'status': 'ok'})

@csrf_exempt
def get_min_order(request):
    data = json.loads(request.body)
    slug = WalletPair.objects.get(id=data.get('wallet_pair_id')).slug
    all_min_order = PairExchangeMapping.objects.filter(
        normalized_name = slug, 
        exchange__in=data.get('exchange_ids', [])
    ).values_list('min_order', flat=True)
    return JsonResponse({
            'success': True,
            'min_order': max(all_min_order),
        })
        