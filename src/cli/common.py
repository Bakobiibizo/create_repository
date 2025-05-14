"""
Common utilities for the ComAI Client CLI.

This module provides common utilities and shared functionality for the CLI commands.
It includes context management, output formatting, and other shared utilities.
"""

import json
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Initialize rich console
console = Console()

# Global context object
global_context = None


@dataclass
class GlobalContext:
    """Global context for CLI commands."""
    
    verbose: bool = False
    json_output: bool = False
    config_path: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)


def get_global_context() -> GlobalContext:
    """
    Get the global context object.
    
    Returns:
        GlobalContext: The global context object.
    """
    if global_context is None:
        raise RuntimeError("Global context not initialized")
    return global_context


def format_output(data: Any, title: Optional[str] = None) -> None:
    """
    Format and print output based on global context settings.
    
    Args:
        data: The data to format and print.
        title: Optional title for the output.
    """
    ctx = get_global_context()
    
    if ctx.json_output:
        # Output as JSON without Rich formatting
        if isinstance(data, dict):
            print(json.dumps(data, indent=2))
        else:
            print(json.dumps({"result": data}, indent=2))
    else:
        # Rich formatted output
        if isinstance(data, dict):
            if title:
                console.print(Panel.fit(f"[bold]{title}[/bold]"))
            
            table = Table(show_header=True, header_style="bold")
            table.add_column("Key")
            table.add_column("Value")
            
            for key, value in data.items():
                table.add_row(str(key), str(value))
            
            console.print(table)
        else:
            if title:
                console.print(f"[bold]{title}:[/bold] {data}")
            else:
                console.print(data)


def get_client():
    """
    Get a client instance for interacting with the blockchain.
    
    Returns:
        CommuneClient: A client instance.
    """
    from src.blockchain_interface.client import CommuneClient
    from src.utilities.environment_manager import get_environment_manager
    
    env_manager = get_environment_manager()
    node_url = env_manager.get_var("COMAI_NODE_URL", "ws://127.0.0.1:9944")
    
    return CommuneClient(url=node_url)


def format_balance(balance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format balance information for display.
    
    Args:
        balance: Raw balance information from the blockchain.
        
    Returns:
        Dict[str, Any]: Formatted balance information.
    """
    # Convert raw balance values to a more readable format
    formatted = {}
    
    if "free" in balance:
        formatted["Free"] = balance["free"]
    
    if "reserved" in balance:
        formatted["Reserved"] = balance["reserved"]
    
    if "frozen" in balance:
        formatted["Frozen"] = balance["frozen"]
    
    if "flags" in balance:
        formatted["Flags"] = balance["flags"]
    
    # Calculate total balance
    total = 0
    if "free" in balance:
        total += balance["free"]
    if "reserved" in balance:
        total += balance["reserved"]
    
    formatted["Total"] = total
    
    return formatted
