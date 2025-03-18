import os
import json
import logging
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import asyncio
import websockets
from utils import hex_to_base64, check_environment_variables, BB_CONTRACT_ADDRESS, ERC20_ABI, BB_ABI, CURRENCIES_DATA

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
USER_ID = os.getenv("USER_ID")
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


def parse_units(amount, decimals):
    return int(amount * (10 ** decimals))


async def send_allowance(amount, currency_id):
    try:
        currency = CURRENCIES_DATA[currency_id]
        if not currency['contract']:
            raise ValueError("Contract address is missing for the selected currency.")

        erc20_contract = web3.eth.contract(address=currency['contract'], abi=ERC20_ABI)
        amount_unit = parse_units(amount, currency['decimals'])

        tx_without_gas = erc20_contract.functions.approve(
            BB_CONTRACT_ADDRESS, amount_unit
        ).build_transaction({
            'chainId': 1,  # Mainnet
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(account.address)
        })

        estimated_gas = get_dynamic_gas(tx_without_gas)

        transaction = erc20_contract.functions.approve(
            BB_CONTRACT_ADDRESS, amount_unit
        ).build_transaction({
            'chainId': 1,  # Mainnet
            'gas': estimated_gas,
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(account.address)
        })

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logging.info(f"Approve transaction sent, hash: {web3.to_hex(tx_hash)}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        logging.info("Approve transaction confirmed: %s", receipt)
    except Exception as e:
        logging.error(f"Error in send_allowance: {e}")
        raise


async def send_deposit(amount, currency_id):
    try:
        currency = CURRENCIES_DATA[currency_id]
        if not currency['contract']:
            raise ValueError("Contract address is missing for the selected currency.")

        main_contract = web3.eth.contract(address=BB_CONTRACT_ADDRESS, abi=BB_ABI)
        amount_unit = parse_units(amount, currency['decimals'])

        tx_without_gas = main_contract.functions.depositERC(
            amount_unit,
            currency['contract'],
            currency_id,
            int(USER_ID)
        ).build_transaction({
            'chainId': 1,
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(account.address)
        })

        estimated_gas = get_dynamic_gas(tx_without_gas)

        transaction = main_contract.functions.depositERC(
            amount_unit,
            currency['contract'],
            currency_id,
            int(USER_ID)
        ).build_transaction({
            'chainId': 1,
            'gas': estimated_gas,
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(account.address)
        })

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logging.info(f"Deposit transaction sent, hash: {web3.to_hex(tx_hash)}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        logging.info("Deposit transaction confirmed: %s", receipt)
        return web3.to_hex(tx_hash)
    except Exception as e:
        logging.error(f"Error in send_deposit: {e}")
        raise


async def claim_deposit(deposit_hash, amount, currency_id):
    try:
        # ATTENTION: Make sure that all parameters are in alphabetical order.
        issuance_data = {
            "Currency": {"ID": currency_id},
            "Deposit": {"Amount": amount, "TXID": deposit_hash, "UserID": USER_ID},
            "MinerFeeStr": "0.00001",
            "NodeID": NODE_ID,
            "UserID": USER_ID
        }

        message = json.dumps(issuance_data)
        signature = web3.eth.account.sign_message(encode_defunct(text=message), private_key=PRIVATE_KEY).signature

        ws_message = {
            "Type": "CurrencyIssuance",
            "SignatureUser": hex_to_base64(signature.hex()),
            "Data": issuance_data
        }

        async with websockets.connect(NODE_URL) as ws:
            await ws.send(json.dumps(ws_message))
            async for msg in ws:
                response = json.loads(msg)
                if response.get("Type") == "CurrencyIssuance":
                    logging.info("Currency issuance status: %s", response.get("State"))
                    break
    except Exception as e:
        logging.error(f"Error in claim_deposit: {e}")
        raise


if __name__ == "__main__":
    currency_id = 2  # WBTC
    amount = 0.00001  # Example amount

    try:
        asyncio.run(send_allowance(amount, currency_id))
        deposit_hash = asyncio.run(send_deposit(amount, currency_id))
        asyncio.run(claim_deposit(deposit_hash, amount, currency_id))
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
