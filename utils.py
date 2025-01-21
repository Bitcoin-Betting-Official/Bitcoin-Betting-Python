import os
from dotenv import load_dotenv
import base64

# Constants
BB_CONTRACT_ADDRESS = '0x5978C6153A06B141cD0935569F600a83Eb44AeAa'

BB_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "userId", "type": "uint256"}
        ],
        "name": "deposit",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "amount", "type": "uint256"},
            {"name": "tokenAddress", "type": "address"},
            {"name": "currency", "type": "uint8"},
            {"name": "userid", "type": "uint256"}
        ],
        "name": "depositERC",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "amount", "type": "uint256"},
            {"name": "nonce", "type": "uint256"},
            {"name": "receiver", "type": "address"},
            {"name": "currency", "type": "uint8"},
            {"name": "txid", "type": "bytes32"},
            {"name": "signature", "type": "bytes"}
        ],
        "name": "withdraw",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "amount", "type": "uint256"},
            {"name": "nonce", "type": "uint256"},
            {"name": "tokenAddress", "type": "address"},
            {"name": "currency", "type": "uint8"},
            {"name": "receiver", "type": "address"},
            {"name": "txid", "type": "bytes32"},
            {"name": "signature", "type": "bytes"}
        ],
        "name": "withdrawERC",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"}
        ],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

CURRENCIES_DATA = [
    {"id": 0, "decimals": 18, "contract": ''},
    {"id": 1, "decimals": 18},
    {"id": 2, "decimals": 8, "contract": '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'}
]


def unix_to_ticks(unix: int) -> int:
    return unix * 10000 + 621355968000000000

def hex_to_base64(hex_str: str) -> str:
    binary = bytes.fromhex(hex_str)
    return base64.b64encode(binary).decode('utf-8')

def check_environment_variables():
    load_dotenv()

    required_vars = [
        "PRIVATE_KEY", "RPC_ENDPOINT", "USER_ID", "NODE_ID", "NODE_URL"
    ]

    for var in required_vars:
        if not os.getenv(var):
            raise EnvironmentError(f"{var} environment variable not found.")
