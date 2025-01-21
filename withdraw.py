import os
import time
import json
import logging
import asyncio
import websockets
import uuid
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from utils import unix_to_ticks, hex_to_base64, BB_ABI, BB_CONTRACT_ADDRESS, CURRENCIES_DATA, \
    check_environment_variables

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

# Wallet and Node Configuration
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
USER_ID = os.getenv("USER_ID")
NODE_ID = os.getenv("NODE_ID")
NODE_URL = os.getenv("NODE_URL")
RPC_ENDPOINT = "https://eth.llamarpc.com"

web3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
try:
    account = Account.from_key(PRIVATE_KEY)
    logging.info("Account initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize account: {e}")
    exit(1)

main_contract = web3.eth.contract(address=BB_CONTRACT_ADDRESS, abi=BB_ABI)

# Operation Configuration
amount = 20  # 0.1 mETH
currency_id = 1  # Currency ID: 'mBTC' = 0, 'mETH' = 1, 'WBTC' = 2


async def request_withdraw():
    try:
        logging.info("Will request a withdraw on Bitcoin Betting.")
        # ATTENTION: Make sure that all parameters are in alphabetical order.
        # ATTENTION: Remove empty string and zeroed number values.
        withdraw_data = {
            "Amount": amount,
            "CreatedByUser": unix_to_ticks(int(time.time() * 1000)),
            "Cur": currency_id,
            "From": USER_ID,
            "ID": str(uuid.uuid4()),
            "MinerFeeStr": "0.00001",
            "NodeID": NODE_ID,
            "Reference": account.address.lower(),
            "TType": 10,
            "UserID": USER_ID
        }

        # Sign the message
        message = json.dumps(withdraw_data)
        signature = web3.eth.account.sign_message(
            encode_defunct(text=message), private_key=PRIVATE_KEY
        ).signature

        # Prepare WebSocket message
        ws_message = {
            "Type": "Transfer",
            "SignatureUser": hex_to_base64(signature.hex()),
            "Data": withdraw_data,
            "UserID": USER_ID
        }

        # Connect to WebSocket and send the message
        async with websockets.connect(NODE_URL) as ws:
            await ws.send(json.dumps(ws_message))
            async for msg in ws:
                response = json.loads(msg)
                if response.get("Type") == "Transfer":
                    logging.info(f"Withdraw request status: {response['State']}")
                    return response
    except Exception as e:
        logging.error(f"Error in request_withdraw: {e}")
        raise


async def send_withdraw():
    try:
        async with websockets.connect(NODE_URL) as ws:
            message = {
                "Type": "GetBurnValidations",
                "Data": {
                    "MaxResults": 1,
                    "NodeID": NODE_ID,
                    "UserID": USER_ID
                }
            }

            # Send message to fetch burn validations
            await ws.send(json.dumps(message))
            async for msg in ws:
                response = json.loads(msg)
                if response.get("Type") == "GetBurnValidations":
                    logging.info(f"Withdraw request status: {response}")
                    burn_validation = response["Data"][0]
                    if burn_validation["Cur"] == "1":  # ETH Withdraw
                        amount_eth = web3.to_wei(burn_validation["Amount"] / 1000, "ether")
                        request = main_contract.functions.withdraw(
                            amount_eth,
                            int(burn_validation["Nonce"]),
                            account.address,
                            1,
                            f"0x{burn_validation['TXID']}",
                            burn_validation["SignatureValidator"]
                        ).build_transaction({
                            "from": account.address,
                            "gas": 300000,
                            "gasPrice": web3.to_wei("20", "gwei"),
                            "nonce": web3.eth.get_transaction_count(account.address)
                        })
                    else:  # ERC20 Withdraw
                        amount_unit = int(
                            burn_validation["Amount"] / 1000
                            * (10 ** CURRENCIES_DATA[burn_validation["Cur"]]["decimals"])
                        )
                        request = main_contract.functions.withdrawERC(
                            amount_unit,
                            int(burn_validation["Nonce"]),
                            CURRENCIES_DATA[burn_validation["Cur"]]["contract"],
                            CURRENCIES_DATA[burn_validation["Cur"]]["id"],
                            account.address,
                            f"0x{burn_validation['TXID']}",
                            burn_validation["SignatureValidator"]
                        ).build_transaction({
                            "from": account.address,
                            "gas": 300000,
                            "gasPrice": web3.to_wei("20", "gwei"),
                            "nonce": web3.eth.get_transaction_count(account.address)
                        })

                    # Sign and send transaction
                    signed_tx = web3.eth.account.sign_transaction(request, PRIVATE_KEY)
                    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    logging.info(f"Withdraw transaction monitoring: {web3.to_hex(tx_hash)}")
                    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    logging.info(f"Withdraw confirmed: {receipt}")
                    break
    except Exception as e:
        logging.error(f"Error in send_withdraw: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(request_withdraw())
        asyncio.run(send_withdraw())
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
