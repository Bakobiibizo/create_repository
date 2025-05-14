"""
Subnet commands for the ComAI Client CLI.

This module provides commands for listing and querying subnets.
"""

import typer
from typing import Optional
from rich.console import Console

from src.cli.common import get_client, format_output

# Initialize console
console = Console()

# Create the subnet app
app = typer.Typer(
    name="subnet",
    help="Manage subnets",
    no_args_is_help=True,
)


@app.command("list")
def list_subnets():
    """
    List all available subnets.
    
    This command queries the blockchain for all available subnets
    and displays them in a list.
    """
    try:
        # Get client
        client = get_client()
        
        # Query subnets
        subnets = client.list_subnets()
        
        # Format and display the result
        from src.cli.common import get_global_context
        
        if get_global_context().json_output:
            # For JSON output, use the raw subnets list without wrapping
            import json
            print(json.dumps(subnets, indent=2))
        else:
            # For human-readable output, use the format_output function
            format_output(subnets, "Available Subnets")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("info")
def subnet_info(
    subnet_id: int = typer.Argument(..., help="The ID of the subnet to query")
):
    """
    Get information about a specific subnet.
    
    This command queries the blockchain for information about the specified subnet
    and displays details such as name, owner, stake, and validators.
    """
    try:
        # Get client
        client = get_client()
        
        # Query subnet info
        info = client.query_subnet_info(subnet_id)
        
        # Format and display the result
        format_output(info, f"Subnet Information: {info['name']} (ID: {subnet_id})")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)
