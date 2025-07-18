import asyncio
import websockets
import json
import PushDataV3ApiWrapper_pb2
from google.protobuf.json_format import MessageToDict


async def handle_order_book(data: bytes):
    try:
        message = PushDataV3ApiWrapper_pb2.PushDataV3ApiWrapper()
        message.ParseFromString(data)

        message_dict = MessageToDict(message, preserving_proto_field_name=True)

        print(f"\nSymbol: {message_dict.get('symbol')}")
        print(f"Channel: {message_dict.get('channel')}")

        if 'publicAggreDepths' in message_dict:
            depth_data = message_dict['publicAggreDepths']
            bids = depth_data.get('bids', [])
            asks = depth_data.get('asks', [])

            print("\n=== Order Book ===")
            print("Top 5 Asks (продажа):")
            for ask in sorted(asks[:5], key=lambda x: float(x['price'])):
                print(f"Price: {ask['price']:<12} Amount: {ask['quantity']}")

            print("\nTop 5 Bids (покупка):")
            for bid in sorted(bids[:5], key=lambda x: float(x['price']), reverse=True):
                print(f"Price: {bid['price']:<12} Amount: {bid['quantity']}")

            print(f"\nVersion: {depth_data.get('fromVersion')} -> {depth_data.get('toVersion')}")
        else:
            print("No order book data found in message")

    except Exception as e:
        print(f"Error parsing data: {str(e)}")


async def subscribe_order_book():
    uri = "wss://wbs-api.mexc.com/ws"
    symbol = "BTCUSDT"
    channel = f"spot@public.aggre.depth.v3.api.pb@10ms@{symbol}"

    while True:
        try:
            async with websockets.connect(uri) as ws:
                sub_msg = {
                    "method": "SUBSCRIPTION",
                    "params": [channel]
                }
                await ws.send(json.dumps(sub_msg))
                print(f"Successfully subscribed to {channel}")

                while True:
                    data = await ws.recv()
                    if isinstance(data, str):
                        print("Server response:", data)
                        continue

                    await handle_order_book(data)

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed, reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Connection error: {str(e)}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    print("Starting MEXC WebSocket client...")
    asyncio.run(subscribe_order_book())