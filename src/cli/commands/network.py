"""
Network commands for the ComAI Client CLI.

This module provides commands for querying network status and information.
"""

import typer
from typing import Optional
from rich.console import Console

from src.cli.common import get_client, format_output

# Initialize console
console = Console()

# Create the network app
app = typer.Typer(
    name="network",
    help="Interact with the blockchain network",
    no_args_is_help=True,
)


@app.command("status")
def status():
    """
    Get the current status of the blockchain network.
    
    This command queries the blockchain for the current network status
    and displays information such as health, peer count, and sync status.
    """
    try:
        # Get client
        client = get_client()
        
        # Query network status
        status = client.query_network_status()
        
        # Format and display the result
        format_output(status, "Network Status")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("info")
def info():
    """
    Get information about the blockchain network.
    
    This command queries the blockchain for network information such as
    chain name, version, and system properties.
    """
    try:
        # Get client
        client = get_client()
        
        # Query network information
        chain = client.query_system_chain()
        version = client.query_system_version()
        properties = client.query_system_properties()
        
        # Combine the results
        info = {
            "chain": chain,
            "version": version,
            "properties": properties
        }
        
        # Format and display the result
        format_output(info, "Network Information")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)
