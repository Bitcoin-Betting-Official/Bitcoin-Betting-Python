import os
import time
import json
import logging
import asyncio
import websockets
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from utils import hex_to_base64, unix_to_ticks, check_environment_variables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Check environment variables
try:
    check_environment_variables()
except Exception as e:
    logging.error(f"Environment variable check failed: {e}")
    exit(1)

# Wallet Config
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
USER_ID = os.getenv("USER_ID")
NODE_URL = os.getenv("NODE_URL")
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT")

web3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
try:
    account = Account.from_key(PRIVATE_KEY)
    logging.info("Account initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize account: {e}")
    exit(1)

# Operation Config
maker_order_id = "9099a901-9180-4869-afb7-e1cc88c2c169"
market_id = "6904d2c0-72c1-4f6b-987f-6843f4b19663"
amount = 1.392  # 0.01 mWBTC
price = 1.359   # Decimal odds
side = 1        # 1 = Buy, 2 = Sell

async def place_order():
    try:
        logging.info("Will place an order on Bitcoin betting.")

        # ATTENTION: Make sure that all parameters are in alphabetical order.
        order_data = {
            "CreatedByUser": unix_to_ticks(int(time.time() * 1000)),
            "MinerFeeStr": "0.00001",
            "UnmatchedOrder": {
                "Amount": amount,
                "ID": maker_order_id,
                "Price": price,
                "RemAmount": amount,
                "Side": side,
                "Type": 2
            },
            "UserID": USER_ID,
            "UserOrder": {
                "MarketID": market_id
            }
        }

        # Sign the message
        message = json.dumps(order_data)
        signature = web3.eth.account.sign_message(
            encode_defunct(text=message), private_key=PRIVATE_KEY
        ).signature

        # Prepare WebSocket message
        ws_message = {
            "Type": "OrderAlteration",
            "SignatureUser": hex_to_base64(signature.hex()),
            "Data": order_data
        }

        # Connect to WebSocket and send message
        async with websockets.connect(NODE_URL) as ws:
            await ws.send(json.dumps(ws_message))
            async for msg in ws:
                response = json.loads(msg)
                if response.get("Type") == "OrderAlteration":
                    logging.info(f"Order Placement Status: {response}")
                    break
    except Exception as e:
        logging.error(f"Error in place_order: {e}")
        raise


async def make_transfer():
    try:
        logging.info("Will make a transfer on Bitcoin betting.")

        # ATTENTION: Make sure that all parameters are in alphabetical order.
        order_data = {
            "Amount": 0.01,
            "CreatedByUser": unix_to_ticks(int(time.time() * 1000)),
            "From": 9,
            "ID": maker_order_id,
            "MinerFeeStr": "0.00001",
            "NodeID": 102,
            "To": 12,
            "UserID": 9,
        }

        # Sign the message
        message = json.dumps(order_data,separators=(',', ':'))

        logging.info(message)
        signature = web3.eth.account.sign_message(
            encode_defunct(text=message), private_key=PRIVATE_KEY
        ).signature

        # Prepare WebSocket message
        ws_message = {
            "Type": "Transfer",
            "SignatureUser": hex_to_base64(signature.hex()),
            "Data": order_data
        }

        # Connect to WebSocket and send message
        async with websockets.connect(NODE_URL) as ws:
            await ws.send(json.dumps(ws_message))
            async for msg in ws:
                response = json.loads(msg)
                if response.get("Type") == "Transfer":
                    logging.info(f"Transfer Status: {response}")
                    break
    except Exception as e:
        logging.error(f"Error in place_order: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(place_order())
