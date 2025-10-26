import requests


def get_simple_gate_futures_list():
    """Простой список всех фьючерсных монет на Gate"""

    url = "https://api.gateio.ws/api/v4/futures/usdt/contracts"
    response = requests.get(url)
    contracts = response.json()

    coins = []
    for contract in contracts:
        if contract.get('status') == 'trading':
            coins.append({
                'name': contract['name'],
                'base': contract.get('base', ''),
                'contract_size': contract.get('quanto_multiplier', 1),
                'min_order': contract.get('min_base_currency', 0)
            })

    # Сортируем по названию монеты
    coins.sort(key=lambda x: x['base'])

    print(f"🎯 Всего торговых пар: {len(coins)}")
    print("\nСписок монет:")

    # Выводим по 8 монет в строке
    coin_names = [coin['base'] for coin in coins]
    for i in range(0, len(coin_names), 8):
        print('  '.join(coin_names[i:i + 8]))


# Быстрый запуск
get_simple_gate_futures_list()