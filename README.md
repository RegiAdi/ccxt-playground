# CCXT Playground

A powerful CLI tool to test and explore CCXT exchange endpoints with detailed request/response information.

## Features

- 🚀 **Interactive Exchange Selection**: Choose from 100+ supported exchanges
- 🔑 **Optional API Authentication**: Test endpoints with or without API keys
- 📊 **Comprehensive Endpoint Discovery**: Browse all available methods organized by category
- 🧪 **Smart Parameter Handling**: Intelligent defaults and suggestions for common parameters
- 📝 **Detailed Request/Response Logging**: See exactly what was sent and received
- 🎨 **Beautiful Terminal UI**: Rich formatting with tables, panels, and syntax highlighting
- 🔄 **Non-Interactive Mode**: Use command-line arguments for automation

## Installation

### Prerequisites

- Python 3.13 or higher
- `uv` package manager (recommended) or `pip`

### Using uv (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ccxt-playground

# Install dependencies
uv sync

# Run the tool
uv run main.py

# Or install and use the CLI command
uv pip install -e .
uv run ccxt-test
```

### Using pip

```bash
# Clone the repository
git clone <repository-url>
cd ccxt-playground

# Install dependencies
pip install -e .

# Run the tool
python main.py

# Or use the CLI command
uv run ccxt-test
```

## Usage

### CLI Command Installation

After installing dependencies, you can install the CLI tool globally:

```bash
# Install the CLI command
uv pip install -e .

# Now you can use the command from anywhere
uv run ccxt-test --help
uv run ccxt-test --exchange binance --endpoint fetch_ticker
```

### Interactive Mode (Default)

Run the tool without arguments to enter interactive mode:

```bash
# Using uv run
uv run main.py

# Using the installed CLI command
uv run ccxt-test
```

The tool will guide you through:
1. **Exchange Selection**: Choose from available exchanges
2. **API Credentials**: Optionally provide API key and secret
3. **Endpoint Testing**: Browse and test various endpoints

### Non-Interactive Mode

Use command-line arguments for automation:

```bash
# Test a specific endpoint
uv run main.py --exchange indodax --endpoint fetch_ticker --symbol BTC/IDR

# With authentication
uv run main.py --exchange indodax --api-key YOUR_KEY --secret YOUR_SECRET --endpoint fetch_balance

# Or using the CLI command
uv run ccxt-test --exchange indodax --endpoint fetch_ticker --symbol BTC/IDR
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--exchange` | `-e` | Exchange name to use | None |
| `--api-key` | | API key for authentication | None |
| `--secret` | | Secret key for authentication | None |
| `--endpoint` | | Specific endpoint to test | None |
| `--symbol` | | Symbol to use for testing | BTC/IDR |
| `--limit` | | Limit for pagination | 10 |

## Examples

### Testing Market Data

```bash
# Get ticker information
uv run main.py --exchange indodax --endpoint fetch_ticker --symbol BTC/IDR

# Get order book
uv run main.py --exchange coinbase --endpoint fetch_order_book --symbol BTC/USD

# Or using the CLI command
uv run ccxt-test --exchange indodax --endpoint fetch_ticker --symbol BTC/IDR

# 💾 After each response, you'll be asked if you want to save it to a JSON file
```

### Testing Trading Endpoints

```bash
# Get open orders (requires authentication)
uv run main.py --exchange indodax --api-key YOUR_KEY --secret YOUR_SECRET --endpoint fetch_open_orders

# Get trading history
uv run main.py --exchange kraken --endpoint fetch_my_trades --symbol BTC/USD

# Or using the CLI command
uv run ccxt-test --exchange indodax --api-key YOUR_KEY --secret YOUR_SECRET --endpoint fetch_open_orders
```

### Testing Account Endpoints

```bash
# Get account balance (requires authentication)
uv run main.py --exchange indodax --api-key YOUR_KEY --secret YOUR_SECRET --endpoint fetch_balance

# Get deposit history
uv run main.py --exchange coinbase --api-key YOUR_KEY --secret YOUR_SECRET --endpoint fetch_deposits

# Or using the CLI command
uv run ccxt-test --exchange indodax --api-key YOUR_KEY --secret YOUR_SECRET --endpoint fetch_balance
```

## Supported Exchanges

The tool supports all exchanges available in CCXT, including:

- **Indonesia-Friendly Exchanges**: Tokocrypto, Indodax, Coinbase, Kraken, KuCoin, OKX, Bybit, Gate
- **Decentralized Exchanges**: Uniswap, PancakeSwap, SushiSwap
- **Traditional Finance**: Interactive Brokers, TD Ameritrade
- **And 100+ more**...

**Note**: The tool defaults to Indodax (Indonesia's largest crypto exchange) and uses IDR pairs by default.

## Endpoint Categories

The tool organizes endpoints into logical categories:

- **Public**: General information endpoints (no authentication required)
- **Market Data**: Price, volume, order book data
- **Trading**: Order management, trading history
- **Account**: Balance, deposits, withdrawals
- **Other**: Miscellaneous utility functions

## Features in Detail

### Smart Parameter Handling

- **Symbols**: Automatically suggests available trading pairs
- **Timestamps**: Accepts "now" for current time or Unix timestamps
- **Limits**: Provides sensible defaults for pagination
- **Booleans**: Accepts "true"/"false" strings

### Error Handling

- Graceful handling of API errors
- Detailed error messages with context
- Option to view full tracebacks for debugging
- Continues operation after errors

### Output Formatting

- **JSON Syntax Highlighting**: Beautiful formatting of API responses
- **Structured Tables**: Clear presentation of request details
- **Response Summaries**: Quick overview of response structure
- **Navigation**: Paginated endpoint browsing
- **Response Export**: Save responses to JSON files with full context
- **Endpoints Export**: Save available endpoints information to JSON files

## Security Best Practices

### 🔐 API Key Security

**⚠️ IMPORTANT: API keys and secrets are NEVER stored permanently**

- **Memory Only**: Credentials are stored only in memory during the active session
- **Automatic Cleanup**: All sensitive data is automatically cleared when you exit
- **No Logging**: API keys are never logged or written to disk
- **Session Isolation**: Each session starts fresh with no credential persistence

### 🚨 Security Warnings

1. **Command Line Arguments**: 
   - API keys passed via `--api-key` and `--secret` flags are visible in shell history
   - Use interactive mode for better security
   - Consider using environment variables for automation

2. **Environment Variables** (Recommended for automation):
   ```bash
   export CCXT_API_KEY='your_api_key'
export CCXT_SECRET='your_secret_key'
uv run ccxt-test --exchange indodax --endpoint fetch_balance
   ```

3. **Interactive Mode**: 
   - Most secure option
   - Credentials are entered via prompts and never stored
   - Perfect for testing and development

### 🛡️ Additional Security Features

- **Credential Validation**: Prompts for confirmation when using command line credentials
- **Memory Clearing**: Explicit cleanup of sensitive data from exchange instances
- **Session Management**: Credentials are cleared when changing exchanges or exiting
- **No Persistent Storage**: No configuration files or databases store credentials

### 📁 Response Export Feature

After each endpoint test, you can optionally save the response to a JSON file:

- **Organized Storage**: All response files are saved to the `responses/` directory
- **Git Ignored**: The responses directory is automatically excluded from version control
- **Automatic Naming**: Files are named with timestamp, exchange, and endpoint
- **Full Context**: Includes both request details and response data
- **Metadata**: Timestamp, exchange, endpoint, and request parameters
- **File Size Info**: Shows file size and warns about large responses
- **Safe Filenames**: Automatically handles special characters in endpoint names

**Example filename**: `responses/ccxt_response_indodax_fetch_ticker_20241201_143022.json`

### 📋 Endpoints Information Export

When viewing available endpoints (Menu option 1), you can save the complete endpoints information:

- **Complete List**: All available endpoints organized by category
- **Method Descriptions**: Docstrings and method information when available
- **Categorized Data**: Public, Market Data, Trading, Account, and Other endpoints
- **Reference File**: Perfect for documentation and analysis
- **Metadata**: Exchange, timestamp, and total endpoint count

**Example filename**: `responses/ccxt_endpoints_indodax_20241201_143022.json`

## Development

### Project Structure

```
ccxt-playground/
├── main.py              # Main CLI application
├── pyproject.toml       # Project configuration and dependencies
├── README.md            # This file
├── .gitignore           # Git ignore rules (excludes responses/)
├── responses/           # Generated response files (git ignored)
└── uv.lock             # Lock file for reproducible builds
```

### Dependencies

- `ccxt`: Cryptocurrency trading library
- `click`: Command-line interface creation kit
- `rich`: Rich text and beautiful formatting in the terminal
- `tabulate`: Pretty-print tabular data

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and testing purposes only. Always test with small amounts and on test networks when possible. The authors are not responsible for any financial losses incurred while using this tool.
