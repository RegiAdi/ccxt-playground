#!/usr/bin/env python3
"""
CCXT Playground - CLI tool to test CCXT exchange endpoints
"""

import ccxt
import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.syntax import Syntax
from tabulate import tabulate
from typing import Dict, Any, List, Optional
import traceback
import os
import sys

console = Console()


class CCXTEndpointTester:
    """Class to handle CCXT endpoint testing"""

    def __init__(self):
        self.exchange = None
        self.exchange_instance = None
        # Store credentials temporarily in memory only
        self._api_key = None
        self._secret = None

    def _clear_credentials(self):
        """Clear credentials from memory"""
        if self._api_key:
            self._api_key = None
        if self._secret:
            self._secret = None

    def get_available_exchanges(self) -> List[str]:
        """Get list of all available CCXT exchanges"""
        return sorted(ccxt.exchanges)

    def select_exchange(self) -> str:
        """Interactive exchange selection"""
        exchanges = self.get_available_exchanges()

        # Show popular exchanges first (Indonesia-friendly)
        popular = [
            "indodax",
            "coinbase",
            "kraken",
            "kucoin",
            "okx",
            "bybit",
            "gate",
            "mexc",
        ]
        popular_exchanges = [ex for ex in popular if ex in exchanges]
        other_exchanges = [ex for ex in exchanges if ex not in popular]

        table = Table(title="Available Exchanges")
        table.add_column("Popular Exchanges", style="cyan")
        table.add_column("Other Exchanges", style="blue")

        # Fill table rows
        max_rows = max(len(popular_exchanges), len(other_exchanges))
        for i in range(max_rows):
            popular_ex = popular_exchanges[i] if i < len(popular_exchanges) else ""
            other_ex = other_exchanges[i] if i < len(other_exchanges) else ""
            table.add_row(popular_ex, other_ex)

        console.print(table)

        while True:
            exchange_name = (
                Prompt.ask("\nEnter exchange name", default="indodax").lower().strip()
            )

            if exchange_name in exchanges:
                return exchange_name
            else:
                console.print(
                    f"[red]Exchange '{exchange_name}' not found. Please try again.[/red]"
                )

    def setup_exchange(
        self, exchange_name: str, api_key: str = "", secret: str = ""
    ) -> None:
        """Initialize exchange instance with optional credentials"""
        try:
            # Store credentials temporarily in memory
            self._api_key = api_key
            self._secret = secret

            exchange_class = getattr(ccxt, exchange_name)

            config = {
                "sandbox": False,
                "verbose": False,
            }

            if api_key:
                config["apiKey"] = api_key
            if secret:
                config["secret"] = secret

            self.exchange_instance = exchange_class(config)
            self.exchange = exchange_name

            # Test basic connection
            if hasattr(self.exchange_instance, "load_markets"):
                try:
                    self.exchange_instance.load_markets()
                    console.print(
                        f"[green]✓ Successfully connected to {exchange_name}[/green]"
                    )
                except Exception as e:
                    console.print(
                        f"[yellow]⚠ Warning: Could not load markets: {str(e)}[/yellow]"
                    )
                    console.print(
                        "[yellow]Some endpoints might not work without proper authentication[/yellow]"
                    )
            else:
                console.print(
                    f"[green]✓ Successfully initialized {exchange_name}[/green]"
                )

        except Exception as e:
            console.print(f"[red]Error setting up exchange: {str(e)}[/red]")
            raise

    def get_available_endpoints(self) -> Dict[str, List[str]]:
        """Get available endpoints grouped by category"""
        if not self.exchange_instance:
            return {}

        endpoints = {
            "Public": [],
            "Market Data": [],
            "Trading": [],
            "Account": [],
            "Other": [],
        }

        # Get all methods from exchange instance
        methods = [
            method
            for method in dir(self.exchange_instance)
            if not method.startswith("_")
            and callable(getattr(self.exchange_instance, method))
        ]

        for method in methods:
            if method in [
                "fetch_ticker",
                "fetch_tickers",
                "fetch_order_book",
                "fetch_ohlcv",
            ]:
                endpoints["Market Data"].append(method)
            elif method.startswith("fetch_") and "order" in method:
                endpoints["Trading"].append(method)
            elif method.startswith("fetch_") and "balance" in method:
                endpoints["Account"].append(method)
            elif method.startswith("fetch_"):
                endpoints["Public"].append(method)
            else:
                endpoints["Other"].append(method)

        return endpoints

    def display_endpoints(self) -> None:
        """Display available endpoints in a table"""
        endpoints = self.get_available_endpoints()

        for category, methods in endpoints.items():
            if methods:
                table = Table(title=f"{category} Endpoints")
                table.add_column("Method", style="cyan")
                table.add_column("Description", style="white")

                for method in sorted(methods):
                    # Get method description from docstring if available
                    method_obj = getattr(self.exchange_instance, method)
                    doc = method_obj.__doc__ or "No description available"
                    description = (
                        doc.split("\n")[0][:60] + "..." if len(doc) > 60 else doc
                    )

                    table.add_row(method, description)

                console.print(table)
                console.print()

        # Ask if user wants to save endpoints info to JSON
        if endpoints:
            console.print("=" * 60)
            console.print("[bold]💾 Save endpoints information to JSON file?[/bold]")
            if Confirm.ask("Save all endpoints data for reference?"):
                self._save_endpoints_info_to_file(endpoints)

    def check_supported_endpoints(self) -> None:
        """Check which endpoints are actually supported by the exchange using the 'has' property"""
        if not self.exchange_instance:
            console.print("[red]No exchange instance available[/red]")
            return

        console.print(
            f"\n[bold cyan]Checking supported endpoints for {self.exchange}[/bold cyan]"
        )

        # Get the 'has' dictionary which shows what's actually supported
        has_dict = getattr(self.exchange_instance, "has", {})

        if not has_dict:
            console.print(
                "[yellow]Exchange doesn't provide capability information[/yellow]"
            )
            return

        # Categorize endpoints by support status
        supported = {}
        not_supported = {}
        emulated = {}

        # Common endpoint categories
        categories = {
            "Market Data": [
                "fetchMarkets",
                "fetchCurrencies",
                "fetchTicker",
                "fetchTickers",
                "fetchOrderBook",
                "fetchOHLCV",
                "fetchTrades",
                "fetchStatus",
            ],
            "Trading": [
                "createOrder",
                "cancelOrder",
                "cancelAllOrders",
                "editOrder",
                "fetchOrder",
                "fetchOrders",
                "fetchOpenOrders",
                "fetchClosedOrders",
            ],
            "Account": [
                "fetchBalance",
                "fetchMyTrades",
                "fetchLedger",
                "fetchTransactions",
                "fetchDeposits",
                "fetchWithdrawals",
                "fetchDepositAddress",
            ],
            "Advanced": [
                "fetchPositions",
                "fetchFundingRate",
                "fetchFundingHistory",
                "fetchBorrowRate",
                "fetchTradingFee",
                "fetchTradingFees",
            ],
            "WebSocket": [
                "ws",
                "watchTicker",
                "watchTickers",
                "watchOrderBook",
                "watchTrades",
                "watchOHLCV",
                "watchBalance",
                "watchOrders",
            ],
        }

        for category, endpoints in categories.items():
            supported[category] = []
            not_supported[category] = []
            emulated[category] = []

            for endpoint in endpoints:
                if endpoint in has_dict:
                    value = has_dict[endpoint]
                    if value is True:
                        supported[category].append(endpoint)
                    elif value == "emulated":
                        emulated[category].append(endpoint)
                    else:
                        not_supported[category].append(endpoint)
                else:
                    not_supported[category].append(endpoint)

        # Display results in organized tables
        for category in categories.keys():
            if supported[category] or emulated[category] or not_supported[category]:
                table = Table(title=f"{category} Endpoints Support Status")
                table.add_column("Endpoint", style="white", width=25)
                table.add_column("Status", style="white", width=15)
                table.add_column("Notes", style="dim", width=30)

                # Add supported endpoints
                for endpoint in supported[category]:
                    table.add_row(
                        endpoint, "[green]✓ Supported[/green]", "Native implementation"
                    )

                # Add emulated endpoints
                for endpoint in emulated[category]:
                    table.add_row(
                        endpoint,
                        "[yellow]⚡ Emulated[/yellow]",
                        "Implemented via other methods",
                    )

                # Add not supported endpoints
                for endpoint in not_supported[category]:
                    table.add_row(
                        endpoint, "[red]✗ Not Supported[/red]", "Not available"
                    )

                console.print(table)
                console.print()

        # Summary statistics
        total_supported = sum(len(endpoints) for endpoints in supported.values())
        total_emulated = sum(len(endpoints) for endpoints in emulated.values())
        total_not_supported = sum(
            len(endpoints) for endpoints in not_supported.values()
        )
        total_checked = total_supported + total_emulated + total_not_supported

        summary_table = Table(title=f"Support Summary for {self.exchange}")
        summary_table.add_column("Status", style="bold")
        summary_table.add_column("Count", style="bold", justify="right")
        summary_table.add_column("Percentage", style="bold", justify="right")

        if total_checked > 0:
            summary_table.add_row(
                "[green]Fully Supported[/green]",
                str(total_supported),
                f"{(total_supported/total_checked)*100:.1f}%",
            )
            summary_table.add_row(
                "[yellow]Emulated[/yellow]",
                str(total_emulated),
                f"{(total_emulated/total_checked)*100:.1f}%",
            )
            summary_table.add_row(
                "[red]Not Supported[/red]",
                str(total_not_supported),
                f"{(total_not_supported/total_checked)*100:.1f}%",
            )

        console.print(summary_table)

        # Additional exchange info
        console.print(f"\n[bold]Exchange Information:[/bold]")
        info_table = Table()
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="white")

        info_table.add_row("Exchange ID", self.exchange)
        info_table.add_row(
            "API Version", getattr(self.exchange_instance, "version", "Unknown")
        )
        info_table.add_row(
            "Rate Limit",
            f"{getattr(self.exchange_instance, 'rateLimit', 'Unknown')} ms",
        )

        # Check if sandbox mode is available
        if hasattr(self.exchange_instance, "sandbox"):
            info_table.add_row(
                "Sandbox Mode",
                "✓ Available" if self.exchange_instance.sandbox else "✗ Not enabled",
            )

        console.print(info_table)

        # Ask if user wants to save the capability info
        console.print("\n" + "=" * 60)
        console.print("[bold]💾 Save endpoint support information to JSON file?[/bold]")
        if Confirm.ask("Save endpoint capabilities data for reference?"):
            self._save_capability_info_to_file(
                has_dict, supported, emulated, not_supported
            )

    def _save_capability_info_to_file(
        self, has_dict: dict, supported: dict, emulated: dict, not_supported: dict
    ) -> None:
        """Save endpoint capability information to a JSON file"""
        try:
            import os
            from datetime import datetime

            # Ensure responses directory exists
            responses_dir = "responses"
            os.makedirs(responses_dir, exist_ok=True)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ccxt_capabilities_{self.exchange}_{timestamp}.json"
            filepath = os.path.join(responses_dir, filename)

            # Calculate totals
            total_supported = sum(len(endpoints) for endpoints in supported.values())
            total_emulated = sum(len(endpoints) for endpoints in emulated.values())
            total_not_supported = sum(
                len(endpoints) for endpoints in not_supported.values()
            )
            total_checked = total_supported + total_emulated + total_not_supported

            # Prepare data to save
            data_to_save = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "exchange": self.exchange,
                    "description": "Endpoint capability and support information",
                    "api_version": getattr(
                        self.exchange_instance, "version", "Unknown"
                    ),
                    "rate_limit": getattr(
                        self.exchange_instance, "rateLimit", "Unknown"
                    ),
                    "summary": {
                        "total_checked": total_checked,
                        "supported": total_supported,
                        "emulated": total_emulated,
                        "not_supported": total_not_supported,
                        "support_percentage": (
                            round((total_supported / total_checked) * 100, 1)
                            if total_checked > 0
                            else 0
                        ),
                        "emulated_percentage": (
                            round((total_emulated / total_checked) * 100, 1)
                            if total_checked > 0
                            else 0
                        ),
                    },
                },
                "raw_has_dictionary": has_dict,
                "categorized_endpoints": {
                    "supported": supported,
                    "emulated": emulated,
                    "not_supported": not_supported,
                },
            }

            # Save to file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2, default=str, ensure_ascii=False)

            console.print(f"\n[green]✅ Capability info saved to: {filepath}[/green]")
            console.print(
                f"[dim]File contains support status for {total_checked} endpoints[/dim]"
            )

            # Show file size
            file_size = os.path.getsize(filepath)
            if file_size > 1024 * 1024:  # > 1MB
                console.print(
                    f"[yellow]⚠️  File size: {file_size / (1024*1024):.1f} MB[/yellow]"
                )
            else:
                console.print(f"[dim]File size: {file_size / 1024:.1f} KB[/dim]")

        except Exception as e:
            console.print(
                f"\n[red]❌ Error saving capability info to file: {str(e)}[/red]"
            )
            console.print("[yellow]Capability info was not saved[/yellow]")

    def _save_endpoints_info_to_file(self, endpoints: Dict[str, List[str]]) -> None:
        """Save endpoints information to a JSON file"""
        try:
            import os
            from datetime import datetime

            # Ensure responses directory exists
            responses_dir = "responses"
            os.makedirs(responses_dir, exist_ok=True)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ccxt_endpoints_{self.exchange}_{timestamp}.json"
            filepath = os.path.join(responses_dir, filename)

            # Prepare data to save
            data_to_save = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "exchange": self.exchange,
                    "description": "Available endpoints information",
                    "total_endpoints": sum(
                        len(methods) for methods in endpoints.values()
                    ),
                },
                "endpoints": endpoints,
            }

            # Save to file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2, default=str, ensure_ascii=False)

            console.print(f"\n[green]✅ Endpoints info saved to: {filepath}[/green]")
            console.print(
                f"[dim]File contains {sum(len(methods) for methods in endpoints.values())} endpoint definitions[/dim]"
            )

            # Show file size
            file_size = os.path.getsize(filepath)
            if file_size > 1024 * 1024:  # > 1MB
                console.print(
                    f"[yellow]⚠️  File size: {file_size / (1024*1024):.1f} MB[/yellow]"
                )
            else:
                console.print(f"[dim]File size: {file_size / 1024:.1f} KB[/dim]")

        except Exception as e:
            console.print(
                f"\n[red]❌ Error saving endpoints info to file: {str(e)}[/red]"
            )
            console.print("[yellow]Endpoints info was not saved[/yellow]")

    def _get_endpoint_support_status(self, endpoint: str) -> str:
        """Get support status icon for an endpoint"""
        if not self.exchange_instance:
            return ""

        has_dict = getattr(self.exchange_instance, "has", {})

        if endpoint in has_dict:
            value = has_dict[endpoint]
            if value is True:
                return "[green]✓[/green]"  # Fully supported
            elif value == "emulated":
                return "[yellow]⚡[/yellow]"  # Emulated
            else:
                return "[red]✗[/red]"  # Not supported
        else:
            return "[dim]?[/dim]"  # Unknown status

    def select_endpoint(self) -> str:
        """Interactive endpoint selection with support status indicators"""
        endpoints = self.get_available_endpoints()
        all_methods = []

        for category, methods in endpoints.items():
            if methods:
                all_methods.extend(methods)

        all_methods = sorted(all_methods)

        # Display paginated list with larger page size
        page_size = 50
        current_page = 0

        while True:
            start_idx = current_page * page_size
            end_idx = start_idx + page_size
            current_methods = all_methods[start_idx:end_idx]

            table = Table(
                title=f"Available Endpoints with Support Status (Page {current_page + 1} of {(len(all_methods) + page_size - 1) // page_size})"
            )
            table.add_column("Index", style="cyan", width=6)
            table.add_column("Status", style="white", width=6)
            table.add_column("Method", style="green", width=30)
            table.add_column("Index", style="cyan", width=6)
            table.add_column("Status", style="white", width=6)
            table.add_column("Method", style="green", width=30)

            # Display endpoints in 2 columns (left column first, then right column)
            mid_point = (len(current_methods) + 1) // 2
            left_methods = current_methods[:mid_point]
            right_methods = current_methods[mid_point:]

            for i in range(len(left_methods)):
                left_idx = start_idx + i + 1
                left_method = left_methods[i]
                left_status = self._get_endpoint_support_status(left_method)

                if i < len(right_methods):
                    right_idx = start_idx + mid_point + i + 1
                    right_method = right_methods[i]
                    right_status = self._get_endpoint_support_status(right_method)
                    table.add_row(
                        str(left_idx),
                        left_status,
                        left_method,
                        str(right_idx),
                        right_status,
                        right_method,
                    )
                else:
                    # Last row with only left column
                    table.add_row(str(left_idx), left_status, left_method, "", "", "")

            console.print(table)

            # Add legend for status icons
            console.print(
                "\n[bold]Legend:[/bold] [green]✓[/green] Supported | [yellow]⚡[/yellow] Emulated | [red]✗[/red] Not Supported | [dim]?[/dim] Unknown"
            )

            # Navigation instructions
            if current_page > 0:
                console.print("\n[blue]Press 'p' for previous page[/blue]")
            if end_idx < len(all_methods):
                console.print("[blue]Press 'n' for next page[/blue]")
            console.print("[blue]Press 'enter' to input endpoint number[/blue]")
            console.print("[blue]Press 'q' to return to main menu[/blue]")
            console.print("[dim]Press any key to continue...[/dim]")

            # Single key input without Enter
            import sys

            try:
                if os.name == "nt":  # Windows
                    import msvcrt

                    key = msvcrt.getch().decode("utf-8").lower()
                else:  # Unix/Linux/macOS
                    import tty
                    import termios

                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    try:
                        tty.setraw(sys.stdin.fileno())
                        key = sys.stdin.read(1).lower()
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

                # Handle navigation keys
                if key == "q":
                    return None
                elif key == "p" and current_page > 0:
                    current_page -= 1
                    continue
                elif key == "n" and end_idx < len(all_methods):
                    current_page += 1
                    continue
                elif key == "\r" or key == "\n":  # Enter key pressed
                    console.print("\n[blue]Enter endpoint number:[/blue]")
                    full_choice = Prompt.ask(f"Endpoint number (1-{len(all_methods)})")

                    if full_choice.isdigit():
                        idx = int(full_choice) - 1
                        if 0 <= idx < len(all_methods):
                            return all_methods[idx]
                        else:
                            console.print(
                                f"[red]Invalid endpoint number. Must be 1-{len(all_methods)}[/red]"
                            )
                    else:
                        console.print(
                            "[red]Invalid input. Please enter a number.[/red]"
                        )
                elif key.isdigit():
                    # For number input, we need to get the full number
                    console.print(f"\n[blue]Selected: {key}[/blue]")
                    console.print(
                        "[dim]Enter full endpoint number and press Enter:[/dim]"
                    )
                    full_choice = Prompt.ask("Endpoint number", default=key)

                    if full_choice.isdigit():
                        idx = int(full_choice) - 1
                        if 0 <= idx < len(all_methods):
                            return all_methods[idx]
                        else:
                            console.print(
                                f"[red]Invalid endpoint number. Must be 1-{len(all_methods)}[/red]"
                            )
                    else:
                        console.print(
                            "[red]Invalid input. Please enter a number.[/red]"
                        )
                else:
                    # Any other key continues to next page or stays on current
                    if end_idx < len(all_methods):
                        current_page += 1
                    continue

            except (KeyboardInterrupt, EOFError):
                return None
            except Exception as e:
                console.print(f"[red]Navigation error: {str(e)}[/red]")
                continue

    def test_endpoint(self, endpoint: str) -> None:
        """Test a specific endpoint and display results"""
        if not self.exchange_instance:
            console.print("[red]No exchange instance available[/red]")
            return

        method = getattr(self.exchange_instance, endpoint)

        # Get method signature
        import inspect

        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        # Remove 'self' parameter
        if "self" in params:
            params.remove("self")

        console.print(f"\n[bold cyan]Testing endpoint: {endpoint}[/bold cyan]")
        console.print(f"[dim]Parameters: {params}[/dim]")

        # Collect parameters from user
        args = []
        kwargs = {}

        for param in params:
            if param == "symbol":
                # For symbol parameters, show available markets
                try:
                    markets = list(self.exchange_instance.markets.keys())[:10]
                    console.print(
                        f"\n[blue]Available symbols (showing first 10):[/blue]"
                    )
                    console.print(", ".join(markets))
                    value = Prompt.ask(
                        f"Enter {param}", default=markets[0] if markets else "BTC/IDR"
                    )
                except:
                    value = Prompt.ask(f"Enter {param}", default="BTC/IDR")
            elif param == "limit":
                value = Prompt.ask(f"Enter {param}", default="10")
                try:
                    value = int(value)
                except:
                    pass
            elif param == "since":
                value = Prompt.ask(f"Enter {param} (timestamp or 'now')", default="now")
                if value.lower() == "now":
                    import time

                    value = int(time.time() * 1000)
                else:
                    try:
                        value = int(value)
                    except:
                        pass
            else:
                value = Prompt.ask(f"Enter {param}", default="")
                if value.lower() == "none":
                    value = None
                elif value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False

            if param in ["symbol", "limit", "since"]:
                args.append(value)
            else:
                kwargs[param] = value

        # Execute the method
        try:
            console.print(
                f"\n[bold]Executing: {endpoint}({', '.join(map(str, args))}, {kwargs})[/bold]"
            )

            result = method(*args, **kwargs)

            # Display request info (without sensitive data)
            request_info = {
                "Exchange": self.exchange,
                "Endpoint": endpoint,
                "Arguments": args,
                "Keyword Arguments": kwargs,
                "Method": f"{endpoint}({', '.join(map(str, args))}, {kwargs})",
            }

            request_table = Table(title="Request Details")
            request_table.add_column("Field", style="cyan")
            request_table.add_column("Value", style="white")

            for key, value in request_info.items():
                request_table.add_row(key, str(value))

            console.print(request_table)

            # Display response
            console.print(f"\n[bold green]Response:[/bold green]")

            if result is None:
                console.print("[yellow]No response data[/yellow]")
            else:
                # Try to format as JSON
                try:
                    formatted_result = json.dumps(result, indent=2, default=str)
                    syntax = Syntax(formatted_result, "json", theme="monokai")
                    console.print(syntax)
                except:
                    # Fallback to string representation
                    console.print(Panel(str(result), title="Response Data"))

                # Show response summary
                if isinstance(result, dict):
                    console.print(
                        f"\n[blue]Response contains {len(result)} keys[/blue]"
                    )
                    if len(result) <= 10:
                        for key in result.keys():
                            console.print(f"  - {key}")
                    else:
                        console.print(f"  - {', '.join(list(result.keys())[:10])}...")
                elif isinstance(result, list):
                    console.print(
                        f"\n[blue]Response is a list with {len(result)} items[/blue]"
                    )
                    if result and isinstance(result[0], dict):
                        console.print(
                            f"  - Sample keys: {', '.join(list(result[0].keys())[:5])}"
                        )

                # Ask if user wants to save response to file
                if result is not None:
                    console.print("\n" + "=" * 60)
                    if Confirm.ask("💾 Save response to JSON file?"):
                        self._save_response_to_file(endpoint, result, request_info)

        except Exception as e:
            console.print(f"\n[red]Error executing {endpoint}:[/red]")
            console.print(f"[red]{str(e)}[/red]")

            # Show full traceback in verbose mode
            if Confirm.ask("Show full traceback?"):
                console.print(traceback.format_exc())

    def _save_response_to_file(
        self, endpoint: str, response_data: Any, request_info: Dict[str, Any]
    ) -> None:
        """Save the response data to a JSON file"""
        try:
            import time
            from datetime import datetime

            # Ensure responses directory exists
            responses_dir = "responses"
            os.makedirs(responses_dir, exist_ok=True)

            # Create filename with timestamp and endpoint
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_endpoint = endpoint.replace("/", "_").replace("\\", "_")
            filename = f"ccxt_response_{self.exchange}_{safe_endpoint}_{timestamp}.json"

            # Full path to responses directory
            filepath = os.path.join(responses_dir, filename)

            # Prepare data to save (include request info for context)
            data_to_save = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "exchange": self.exchange,
                    "endpoint": endpoint,
                    "request_info": request_info,
                },
                "response": response_data,
            }

            # Save to file in responses directory
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2, default=str, ensure_ascii=False)

            console.print(f"\n[green]✅ Response saved to: {filepath}[/green]")
            console.print(
                f"[dim]File contains both request context and response data[/dim]"
            )

            # Show file size
            file_size = os.path.getsize(filepath)
            if file_size > 1024 * 1024:  # > 1MB
                console.print(
                    f"[yellow]⚠️  File size: {file_size / (1024*1024):.1f} MB[/yellow]"
                )
            else:
                console.print(f"[dim]File size: {file_size / 1024:.1f} KB[/dim]")

        except Exception as e:
            console.print(f"\n[red]❌ Error saving response to file: {str(e)}[/red]")
            console.print("[yellow]Response data was not saved[/yellow]")

    def cleanup(self):
        """Clean up sensitive data"""
        self._clear_credentials()
        if self.exchange_instance:
            # Clear any stored credentials from the exchange instance
            if hasattr(self.exchange_instance, "apiKey"):
                self.exchange_instance.apiKey = None
            if hasattr(self.exchange_instance, "secret"):
                self.exchange_instance.secret = None
        self.exchange_instance = None
        self.exchange = None


def main():
    """Main CLI function"""
    console.print(
        Panel.fit(
            "[bold cyan]CCXT Playground[/bold cyan]\nCLI tool to test CCXT exchange endpoints",
            border_style="cyan",
        )
    )

    # Security warning
    console.print(
        Panel(
            "[bold red]⚠️  SECURITY WARNING[/bold red]\n"
            "• API keys and secrets are stored in memory only during this session\n"
            "• They are automatically cleared when you exit\n"
            "• Never use --api-key or --secret flags in scripts or shared environments\n"
            "• Consider using environment variables for automation",
            border_style="red",
            title="Security Notice",
        )
    )

    tester = CCXTEndpointTester()

    try:
        # Step 1: Select exchange
        console.print("\n[bold]Step 1: Select Exchange[/bold]")
        exchange_name = tester.select_exchange()

        # Step 2: Get API credentials
        console.print(f"\n[bold]Step 2: API Credentials for {exchange_name}[/bold]")
        console.print(
            "[yellow]Note: Some endpoints work without authentication, others require API keys[/yellow]"
        )
        console.print(
            "[yellow]⚠️  Your credentials will only be stored in memory during this session[/yellow]"
        )

        api_key = Prompt.ask("Enter API Key (optional)", default="")
        secret_key = Prompt.ask("Enter Secret Key (optional)", default="")

        # Step 3: Setup exchange
        console.print(f"\n[bold]Step 3: Setting up {exchange_name}[/bold]")
        tester.setup_exchange(exchange_name, api_key, secret_key)

        # Main loop for testing endpoints
        while True:
            console.print("\n" + "=" * 60)
            console.print("[bold]Available Actions:[/bold]")
            console.print("1. View all available endpoints")
            console.print("2. Check supported endpoints only")
            console.print("3. Test a specific endpoint")
            console.print("4. Change exchange")
            console.print("5. Exit")

            choice = Prompt.ask(
                "Select action", choices=["1", "2", "3", "4", "5"], default="3"
            )

            if choice == "1":
                tester.display_endpoints()
            elif choice == "2":
                tester.check_supported_endpoints()
            elif choice == "3":
                endpoint = tester.select_endpoint()
                if endpoint:
                    tester.test_endpoint(endpoint)
                else:
                    console.print("[yellow]Returning to main menu.[/yellow]")
            elif choice == "4":
                # Clear current credentials before changing exchange
                tester.cleanup()
                exchange_name = tester.select_exchange()
                api_key = Prompt.ask("Enter API Key (optional)", default="")
                secret_key = Prompt.ask("Enter Secret Key (optional)", default="")
                tester.setup_exchange(exchange_name, api_key, secret_key)
            elif choice == "5":
                console.print("[green]Goodbye![/green]")
                break

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {str(e)}[/red]")
        if Confirm.ask("Show full traceback?"):
            console.print(traceback.format_exc())
    finally:
        # Always clean up sensitive data
        tester.cleanup()


@click.command()
@click.option("--exchange", "-e", help="Exchange name to use")
@click.option("--api-key", help="API key for authentication")
@click.option("--secret", help="Secret key for authentication")
@click.option("--endpoint", help="Specific endpoint to test")
@click.option("--symbol", default="BTC/IDR", help="Symbol to use for testing")
@click.option("--limit", default=10, help="Limit for pagination")
def cli(exchange, api_key, secret, endpoint, symbol, limit):
    """CCXT Playground - Test CCXT exchange endpoints"""

    # Security warning for command line usage
    if api_key or secret:
        console.print(
            Panel(
                "[bold red]⚠️  SECURITY WARNING[/bold red]\n"
                "• API keys passed via command line are visible in shell history\n"
                "• Consider using environment variables instead:\n"
                "  export CCXT_API_KEY='your_key'\n"
                "  export CCXT_SECRET='your_secret'\n"
                "• Or use interactive mode for better security",
                border_style="red",
                title="Command Line Security Warning",
            )
        )

        if not Confirm.ask("Continue with command line credentials?"):
            console.print(
                "[yellow]Exiting for security. Use interactive mode instead.[/yellow]"
            )
            sys.exit(1)

    if exchange and endpoint:
        # Non-interactive mode
        tester = CCXTEndpointTester()
        try:
            tester.setup_exchange(exchange, api_key or "", secret or "")
            tester.test_endpoint(endpoint)
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
        finally:
            # Always clean up sensitive data
            tester.cleanup()
    else:
        # Interactive mode
        main()


if __name__ == "__main__":
    main()
