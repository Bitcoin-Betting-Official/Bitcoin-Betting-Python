import os
import json
import logging
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import asyncio
import websockets
from utils import BB_CONTRACT_ADDRESS, BB_ABI, hex_to_base64, unix_to_ticks, check_environment_variables

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

# Initialize Web3 and account
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
USER_ID = int(os.getenv("USER_ID"))
NODE_ID = os.getenv("NODE_ID")
NODE_URL = os.getenv("NODE_URL")
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT")

web3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
try:
    account = Account.from_key(PRIVATE_KEY)
    logging.info("Account initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize account: {e}")
    exit(1)

def parse_ether(amount):
    return web3.to_wei(amount, 'ether')

async def send_deposit(amount):
    try:
        logging.info("Will deposit and monitor transaction.")
        main_contract = web3.eth.contract(address=BB_CONTRACT_ADDRESS, abi=BB_ABI)
        amount_unit = parse_ether(amount)

        transaction = main_contract.functions.deposit(USER_ID).build_transaction({
            'chainId': 1,  # Mainnet
            'gas': 300000,
            'gasPrice': web3.to_wei('20', 'gwei'),
            'nonce': web3.eth.get_transaction_count(account.address),
            'value': amount_unit
        })

        # Sign the transaction
        signed_tx = web3.eth.account.sign_transaction(transaction, PRIVATE_KEY)

        # Send the raw transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logging.info(f"Transaction hash: {web3.to_hex(tx_hash)}")

        # Wait for the transaction receipt
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        logging.info(f"Deposit transaction confirmed: {receipt}")
        return web3.to_hex(tx_hash)
    except Exception as e:
        logging.error(f"Error in send_deposit: {e}")
        raise

async def claim_deposit(deposit_hash, amount):
    try:
        logging.info(f"Will claim onchain deposit made on the Bitcoin Betting: {deposit_hash}")
        nonce = unix_to_ticks(int(web3.eth.get_block('latest')['timestamp'])) // 10

        issuance_data = {
            "Currency": {"ID": 1},  # Example: mETH currency ID
            "Deposit": {
                "Amount": amount * 1000,
                "TXID": deposit_hash.lower(),
                "UserID": os.getenv("USER_ID")
            },
            "MinerFeeStr": "0.00001",
            "NodeID": NODE_ID,
            "UserID": os.getenv("USER_ID")
        }

        message = json.dumps(issuance_data)
        signature = web3.eth.account.sign_message(encode_defunct(text=message), private_key=PRIVATE_KEY).signature

        ws_message = {
            "Nonce": nonce,
            "Type": "CurrencyIssuance",
            "SignatureUser": hex_to_base64(signature.hex()),
            "Data": issuance_data
        }

        async with websockets.connect(NODE_URL) as ws:
            await ws.send(json.dumps(ws_message))
            async for msg in ws:
                response = json.loads(msg)
                if response.get("Type") == "CurrencyIssuance":
                    logging.info(f"Currency issuance status: {response}")
                    break
    except Exception as e:
        logging.error(f"Error in claim_deposit: {e}")
        raise


if __name__ == "__main__":
    amount = 0.001  # 1 mEth - It must be more than 0.1 mETH
    try:
        deposit_hash = asyncio.run(send_deposit(amount))
        asyncio.run(claim_deposit(deposit_hash, amount))
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
