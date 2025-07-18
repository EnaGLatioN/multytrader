import requests


def get_all_mexc_pairs():
    # Делаем запрос к API MEXC
    url = "https://api.mexc.com/api/v3/exchangeInfo"
    response = requests.get(url)
    data = response.json()

    # Извлекаем все торговые пары и преобразуем формат
    pairs = []
    for symbol in data['symbols']:
        # Преобразуем из "BTCUSDT" в "BTC_USDT"
        base = symbol['baseAsset']
        quote = symbol['quoteAsset']
        formatted_pair = f"{base}_{quote}"
        pairs.append(formatted_pair)

    # Выводим результат
    print("Все валютные пары MEXC (через подчеркивание):")
    print("-" * 60)
    for i, pair in enumerate(pairs, 1):
        print(f"{i:>4}. {pair}")


if __name__ == "__main__":
    get_all_mexc_pairs()