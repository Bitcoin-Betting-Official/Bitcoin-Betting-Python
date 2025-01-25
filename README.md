# Readme Documentation

## Disclaimer

The code was provided by an external developer. Use with caution. It is still in developing and has not been tested properly. 
Refer to the C# and Javascript implementation in any case.

## Introduction


This project provides Python examples to interact with the Bitcoin Betting API. It includes functionalities such as depositing funds, requesting withdrawals, placing orders, and subscribing to user balances.


## Prerequisites

- Python 3.9 or later
- Conda (optional but recommended)
- Required Python libraries listed in the `environment.yml` file

## Installation

### Using Conda Environment
1. Install Conda if not already installed: [Conda Installation Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
2. Clone the repository.
3. Create a Conda environment using the `environment.yml` file:
   ```bash
   conda env create -f environment.yml
   ```
4. Activate the environment:
   ```bash
   conda activate bitcoin_betting_python_env
   ```

### Using pip (if Conda is not available)
1. Clone the repository.
2. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables

Create a `.env` file in the project root and set the following environment variables:

```env
PRIVATE_KEY=0x9e...
RPC_ENDPOINT=https://eth.llamarpc.com
NODE_URL=wss://sa.bitcoin-betting.com:82/
NODE_ID=12
USER_ID=123
```

### Explanation of Variables:
- `PRIVATE_KEY`: Your wallet's private key (ensure it's kept secure).
- `RPC_ENDPOINT`: URL for the Ethereum RPC endpoint.
- `NODE_URL`: WebSocket endpoint for Bitcoin Betting API.
- `NODE_ID`: Node ID for Bitcoin Betting.
- `USER_ID`: Unique user ID for API operations.

## Features and Usage

### 1. Deposit ERC20 Tokens
Deposit a specified amount of ERC20 tokens into the platform.

Run:
```bash
python deposit_erc20.py
```
Update the amount and currency in the script before running.

### 2. Deposit ETH
Deposit ETH into the platform.

Run:
```bash
python deposit_eth.py
```
Update the amount in the script before running.

### 3. Withdraw Funds
Request and process withdrawals from the platform.

Run:
```bash
python withdraw.py
```

### 4. Place an Order
Place a trade order on the platform.

Run:
```bash
python place_order.py
```
Update the order configuration (amount, price, market ID) in the script.

### 5. Subscribe to Balance
Fetch and display the user's balance for all available currencies.

Run:
```bash
python get_balance.py
```

## Utilities

### `utils.py`
Contains helper functions and constants used across the project:
- `hex_to_base64(hex_str)`: Converts a hex string to Base64.
- `unix_to_ticks(unix)`: Converts Unix time to ticks.
- `check_environment_variables()`: Verifies the presence of required environment variables.
- Contract ABIs and currency data.

## Example Environment

The following environment variables are used for testing:
```env
PRIVATE_KEY=0x9e...
RPC_ENDPOINT=https://eth.llamarpc.com
NODE_URL=wss://sa.bitcoin-betting.com:82/
NODE_ID=12
USER_ID=123
```

## Optional: Conda Environment File

The `environment.yml` file can be used to recreate the environment with all dependencies, including:
- `web3` for blockchain interaction
- `websockets` for WebSocket communication
- `dotenv` for managing environment variables
- And other supporting libraries

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## Notes

1. **Security**:
   - Never expose your `PRIVATE_KEY` or `.env` file.
   - Use a secure method to manage and store sensitive credentials.

2. **Testing**:
   - Use a test network for initial testing to avoid unnecessary expenses on the mainnet.

3. **Logs**:
   - All operations log detailed information to the console for easier debugging.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
