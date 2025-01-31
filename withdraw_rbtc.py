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
USER_ID = int(os.getenv("USER_ID"))
NODE_ID = int(os.getenv("NODE_ID"))
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
amount = 0.05  # 0.1 mETH
currency_id = 5  # Currency ID: 'mBTC' = 0, 'mETH' = 1, 'WBTC' = 2, RBTC = 5
chain_id = 30


async def reset_limit():
    try:

        main_contract = web3.eth.contract(address=BB_CONTRACT_ADDRESS, abi=BB_ABI)

        gasprice = int(web3.eth.gas_price * 1.2)

        transaction = main_contract.functions.resetWithdrawalLimit().build_transaction({
            'chainId': chain_id,
            'gas': 300000,
            'gasPrice': gasprice,
            'nonce': web3.eth.get_transaction_count(account.address)
        })

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logging.info(f"reset transaction sent, hash: {web3.to_hex(tx_hash)}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        logging.info("reset transaction confirmed: %s", receipt)
        return web3.to_hex(tx_hash)
    except Exception as e:
        logging.error(f"Error in reset withdrawal: {e}")
        raise

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
        message = json.dumps(withdraw_data,separators=(',', ':'))
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
            await ws.send(json.dumps(ws_message,separators=(',', ':')))
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
            gasprice = int(web3.eth.gas_price * 1.2)

            # Send message to fetch burn validations
            sign1=''
            sign2=''
            sing3=''
            fetchedsigns =0
            await ws.send(json.dumps(message))
            async for msg in ws:
                response = json.loads(msg)
                if response.get("Type") == "GetBurnValidations":
                    logging.info(f"Withdraw request status: {response}")
                    burn_validation = response["Data"][0]
                    if burn_validation["Cur"] == currency_id:
                        amount_rbtc = web3.to_wei(burn_validation["Amount"] / 1000, "ether")

                    if burn_validation["ValidatorID"] == 1:
                        sign1 = burn_validation["SignatureValidator"]
                        fetchedsigns  += 1
                    if burn_validation["ValidatorID"] == 2:
                        sign2 = burn_validation["SignatureValidator"]
                        fetchedsigns += 1
                    if burn_validation["ValidatorID"] == 3:
                        sign3 = burn_validation["SignatureValidator"]
                        fetchedsigns += 1
                    if fetchedsigns==2 :
                        break

            request = main_contract.functions.withdraw(
                amount_rbtc,
                int(burn_validation["Nonce"]),
                account.address,
                f"0x{burn_validation['TXID']}",
                sign1,
                sign2,
                sign3
            ).build_transaction({
                "from": account.address,
                "gas": 300000,
                "gasPrice": gasprice,
                "nonce": web3.eth.get_transaction_count(account.address)
            })
            signed_tx = web3.eth.account.sign_transaction(request, PRIVATE_KEY)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logging.info(f"Withdraw transaction monitoring: {web3.to_hex(tx_hash)}")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            logging.info(f"Withdraw confirmed: {receipt}")
    except Exception as e:
        logging.error(f"Error in send_withdraw: {e}")
        raise


if __name__ == "__main__":
    try:        
        #asyncio.run(reset_limit())
        asyncio.run(request_withdraw())
        asyncio.run(send_withdraw())
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
