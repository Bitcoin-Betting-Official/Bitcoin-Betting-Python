import asyncio
import json
import signal
from websockets import connect


async def get_markets(address):
    body = {
        "Type": "SubscribeMarketsByFilter",
        "Data": {
            "MarketFilter": {
                "Cat":2,
                "OnlyActive": True,
                "Status": 1,
                "PageSize": 100
            },
            "SubscribeOrderbooks": True,
        "UserID": -1,
        "NodeID": 1,
        }
    }

    async with connect(address) as websocket:
        # Close the connection when receiving SIGTERM.
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, loop.create_task, websocket.close())
	
        # Send the body with the custom encoder
        await websocket.send(json.dumps(body))

        # Process messages received on the connection.
        async for message in websocket:
            print(f"<<< {message}")

if __name__ == "__main__":
    node_address = "wss://node82.sytes.net:82"    
    asyncio.run(get_markets(node_address))
