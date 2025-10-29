from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from exchange.models import WalletPair


@csrf_exempt
def get_min_profit(request):
    wallet_pair = WalletPair.objects.get(id = request.GET.get('wallet_pair'))
    result = []
    for wallet in wallet_pair.exchange_mappings.all():
        if wallet.exchange.name == 'BYBIT':
            # тут пока сомнения
            result.append(wallet.min_order)
        elif wallet.exchange.name == 'GATE':
            result.append(wallet.min_order)  
    print(result)
    return JsonResponse({'min_profit': max(result)})

