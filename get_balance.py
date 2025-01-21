import os
import json
import asyncio
import websockets
from utils import check_environment_variables

# Check environment variables
check_environment_variables()

# Configuration
CURRENCY_IDS = ['mBTC', 'mETH', 'WBTC']
NODE_URL = os.getenv("NODE_URL")
USER_ID = os.getenv("USER_ID")
NODE_ID = os.getenv("NODE_ID")

async def get_balance():
    try:
        async with websockets.connect(NODE_URL) as ws:
            # Subscribe to balance updates
            await ws.send(json.dumps({
                "Type": "SubscribeBalance",
                "UserID": USER_ID,
                "NodeID": NODE_ID
            }))

            # Listen for messages
            async for message in ws:
                data_object = json.loads(message)
                if data_object.get("Type") == "SubscribeBalance":
                    for idx, curr in enumerate(CURRENCY_IDS):
                        curr_data = data_object.get("Data", {}).get(str(idx))
                        if not curr_data:
                            continue

                        decoded = {
                            "id": str(idx),
                            "symbol": curr,
                            **curr_data
                        }
                        print(decoded)

                    break  # Exit after processing the first message

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    asyncio.run(get_balance())
