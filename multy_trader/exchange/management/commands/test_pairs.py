import requests
import gate_api
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--exchange', type=str, default=None)

    def handle(self, *args, **options):
        all_parsers = {
            'GATE':    self.test_gate,
            'BYBIT':   self.test_bybit,
            'KUCOIN':  self.test_kucoin,
            'BINANCE': self.test_binance,
            'HTX':     self.test_htx,
            'MEXC':    self.test_mexc,
            'BINGX':   self.test_bingx,
            'OURBIT':  self.test_ourbit,
            'OKX':     self.test_okx,
        }

        target = options['exchange']
        if target:
            target = target.upper()
            if target not in all_parsers:
                print(f"неизвестная биржа: {target}")
                return
            parsers = {target: all_parsers[target]}
        else:
            parsers = all_parsers

        for name, func in parsers.items():
            print(f"\n--- {name} ---")
            try:
                pairs = func()
                self._print_stats(pairs)
            except Exception as e:
                print(f"ошибка: {e}")

    def _print_stats(self, pairs):
        if not pairs:
            print("нет данных")
            return

        zero_min        = sum(1 for p in pairs if not float(p['min_order'] or 0))
        zero_coin_count = sum(1 for p in pairs if not float(p['coin_count'] or 0))
        zero_step       = sum(1 for p in pairs if not float(p['step'] or 0))

        print(f"всего: {len(pairs)}, min_order=0: {zero_min}, coin_count=0: {zero_coin_count}, step=0: {zero_step}")

        print("первые 5:")
        for p in pairs[:5]:
            print(f"  {p['local_name']}  min_order={p['min_order']}  coin_count={p['coin_count']}  step={p['step']}  min_notional={p['min_notional']}")

        bad = [p for p in pairs if not float(p['min_order'] or 0) or not float(p['coin_count'] or 0) or not float(p['step'] or 0)]
        if bad:
            print("проблемные:")
            for p in bad[:5]:
                print(f"  {p['local_name']}  min_order={p['min_order']}  coin_count={p['coin_count']}  step={p['step']}  min_notional={p['min_notional']}")

    def test_gate(self):
        configuration = gate_api.Configuration(host="https://fx-api.gateio.ws/api/v4")
        api_instance = gate_api.FuturesApi(gate_api.ApiClient(configuration))
        response = api_instance.list_futures_contracts(settle='usdt')

        result = []
        for resp in response:
            order_size_min = float(resp.order_size_min) if resp.order_size_min else 1
            quanto_multiplier = float(resp.quanto_multiplier) if resp.quanto_multiplier else 1
            result.append({
                'local_name': resp.name,
                'min_order':  order_size_min * quanto_multiplier,
                'coin_count': quanto_multiplier,
                'step':       quanto_multiplier,
                'min_notional': None,
            })
        return result

    def test_bybit(self):
        url = "https://api.bybit.com/v5/market/instruments-info"
        data = requests.get(url, params={"category": "linear", "limit": 1000}).json()
        return [{
            'local_name': s['symbol'],
            'min_order':  float(s['lotSizeFilter']['minOrderQty']),
            'coin_count': 1,
            'step':       float(s['lotSizeFilter']['qtyStep']),
            'min_notional': float(s['lotSizeFilter']['minNotionalValue']) if 'minNotionalValue' in s['lotSizeFilter'] else None,
        } for s in data["result"]["list"]]

    def test_kucoin(self):
        data = requests.get("https://api-futures.kucoin.com/api/v1/contracts/active").json()
        return [{
            'local_name': s['symbol'],
            'min_order':  float(s['lotSize']) * float(s['multiplier']),
            'coin_count': float(s['multiplier']),
            'step':       float(s['multiplier']),
            'min_notional': None,
        } for s in data['data'] if not s.get('isInverse')]

    def test_binance(self):
        data = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo").json()
        result = []
        for s in data['symbols']:
            lot = next((f for f in s['filters'] if f['filterType'] == 'LOT_SIZE'), None)
            notional_filter = next((f for f in s['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None)
            result.append({
                'local_name': s['symbol'],
                'min_order':  float(lot['minQty']) if lot else 0,
                'coin_count': 1,
                'step':       float(lot['stepSize']) if lot else 0,
                'min_notional': float(notional_filter['notional']) if notional_filter else None,
            })
        return result

    def test_htx(self):
        data = requests.get("https://api.hbdm.com/linear-swap-api/v1/swap_contract_info").json()
        return [{
            'local_name': s['contract_code'],
            'min_order':  float(s.get('contract_size', 0)),
            'coin_count': float(s.get('contract_size', 0)),
            'step':       float(s.get('contract_size', 0)),
            'min_notional': None,
        } for s in data['data']]

    def test_mexc(self):
        data = requests.get("https://api.mexc.com/api/v1/contract/detail").json()
        return [{
            'local_name': s['symbol'],
            'min_order':  float(s.get('minVol', 0)) * float(s.get('contractSize', 0)),
            'coin_count': float(s.get('contractSize', 0)),
            'step':       float(s.get('contractSize', 0)),
            'min_notional': None,
        } for s in data['data']]

    def test_bingx(self):
        data = requests.get("https://open-api.bingx.com/openApi/swap/v2/quote/contracts").json()
        return [{
            'local_name': s['symbol'],
            'min_order':  float(s['tradeMinQuantity']),
            'coin_count': float(s['size']),
            'step':       10 ** (-int(s.get('quantityPrecision', 0))),
            'min_notional': float(s['tradeMinUSDT']) if 'tradeMinUSDT' in s else None,
        } for s in data['data']]

    def test_ourbit(self):
        data = requests.get("https://futures.ourbit.com/api/v1/contract/detail").json()
        return [{
            'local_name': s['symbol'],
            'min_order':  float(s.get('minVol', 1)) * float(s.get('contractSize', 0)),
            'coin_count': float(s.get('contractSize', 0)),
            'step':       float(s.get('contractSize', 0)),
            'min_notional': None,
        } for s in data['data']]

    def test_okx(self):
        data = requests.get("https://www.okx.com/api/v5/public/instruments", {'instType': 'SWAP'}).json()
        return [{
            'local_name': s['instId'],
            'min_order':  float(s['ctVal']) * float(s['minSz']),
            'coin_count': float(s['ctVal']),
            'step':       float(s['ctVal']) * float(s['lotSz']),
            'min_notional': None,
        } for s in data['data'] if s['ctType'] == 'linear' and s['settleCcy'] == 'USDT']
