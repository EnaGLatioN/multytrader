from django.conf import settings
import ccxt

def mexc_buy_futures_contract():
    exchange = ccxt.mexc({
        'apiKey': "mx0vgllmG4zm746Oiy",
        'secret': "e7ceff7c31584dad9958f6bab36b53d2",
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',  # Указываем тип торговли - фьючерсы
        }
    })
    order_status = exchange.fetch_order('C02__600297473038323712078', 'AIOUSDT')
    print(order_status)

    # # Загружаем рынки для фьючерсов
    # exchange.load_markets()
    #
    # # Создание рыночного ордера на фьючерсы
    # order = exchange.create_order(
    #     symbol="AIOUSDT",
    #     type='market',
    #     side="buy",
    #     amount=10,  # Количество контрактов
    #     params={
    #         'leverage': 1,  # Плечо (опционально)
    #     }
    # )
    return "er"


print(mexc_buy_futures_contract())