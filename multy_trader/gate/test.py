from __future__ import print_function
import gate_api
from gate_api.exceptions import ApiException, GateApiException

def get_pairs():
    configuration = gate_api.Configuration(
        host="https://api.gateio.ws/api/v4"
    )

    # Создаем экземпляр API-клиента
    api_client = gate_api.ApiClient(configuration)
    # Создаем экземпляр класса API
    api_instance = gate_api.SpotApi(api_client)

    # Указываем валютную пару
    currency_pair = 'USDT_RUB'  # str | Валютная пара

    try:
        # Получаем все валютные пары
        api_response = api_instance.list_currency_pairs()
        for i in api_response:
            id = i.id
            print(id)


    except GateApiException as ex:
        with open('response.txt', 'w') as f:
            f.write("Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message))
        print("Ошибка API Gate записана в файл response.txt")
    except ApiException as e:
        with open('response.txt', 'w') as f:
            f.write("Ошибка при вызове SpotApi->get_currency_pair: %s\n" % e)
        print("Ошибка при вызове API записана в файл response.txt")

def get_ordet_book():
    # Defining the host is optional and defaults to https://api.gateio.ws/api/v4
    # See configuration.py for a list of all supported configuration parameters.
    configuration = gate_api.Configuration(
        host="https://api.gateio.ws/api/v4"
    )

    api_client = gate_api.ApiClient(configuration)
    # Create an instance of the API class
    api_instance = gate_api.SpotApi(api_client)
    currency_pair = 'BTC_USDT'  # str | Currency pair
    interval = '10'  # str | Order depth. 0 means no aggregation is applied. default to 0 (optional) (default to '0')
    limit = 10  # int | Maximum number of order depth data in asks or bids (optional) (default to 10)
    with_id = True  # bool | Return order book ID (optional) (default to False)

    try:
        # Retrieve order book
        api_response = api_instance.list_order_book(currency_pair, interval=interval, limit=limit, with_id=with_id)
        print(api_response)
    except GateApiException as ex:
        print("Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message))
    except ApiException as e:
        print("Exception when calling SpotApi->list_order_book: %s\n" % e)

print(get_ordet_book())