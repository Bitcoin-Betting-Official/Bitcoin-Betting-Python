import os
import random
from datetime import datetime
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from utils import hex_to_base64, check_environment_variables

# Check environment variables
check_environment_variables()

# Initialize Web3 and account
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
web3 = Web3(Web3.HTTPProvider(os.getenv("RPC_ENDPOINT")))
account = Account.from_key(PRIVATE_KEY)

# Generate a nonce using a random number
nonce = random.randint(0, 1000000)

# Get the current timestamp
timestamp = datetime.utcnow().isoformat()

# A message explaining the action being taken
message_text = f"Please, make sure that you are signing this message on Bitcoin Betting domain:\nNonce: {nonce}\nTimestamp: {timestamp}"
message = encode_defunct(text=message_text)

# Request the user's signature
signature = web3.eth.account.sign_message(message, private_key=PRIVATE_KEY).signature

# Hash the message
hash = web3.keccak(text=message_text)

# Recover the public key
public_key = Account.recover_message(message, signature=signature)
base64_public_key = hex_to_base64(public_key[2:])

print("User Public Key:", base64_public_key)
