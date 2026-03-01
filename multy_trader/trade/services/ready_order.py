import os
from typing import Any
from uuid import uuid4
import django
import requests
from dataclasses import dataclass
from exchange.models import Exchange


@dataclass()
class ReadyOrder:
    id: uuid4
    wallet_pair: str
    #coin_count: float
    proxy: str
    profit: float
    shoulder: int
    api_key: str
    secret_key: str
    exchange_name: str
    trade_type: str


class ReadyOrderFactory():
    @staticmethod
    def create_ready_order(wallet_pair, order, entry):
        exchange = order.exchange_account.exchange
        return ReadyOrder(
            id = order.id,
            wallet_pair = wallet_pair,
            proxy = order.proxy,
            profit = entry.profit,
            shoulder = entry.shoulder,
            api_key = order.exchange_account.api_key,
            secret_key = order.exchange_account.secret_key,
            exchange_name = exchange.name,
            trade_type = order.trade_type
        )
