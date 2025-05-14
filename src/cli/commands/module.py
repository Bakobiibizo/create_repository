"""
Module commands for the ComAI Client CLI.

This module provides commands for listing and querying blockchain modules.
"""

import typer
from typing import Optional
from rich.console import Console

from src.cli.common import get_client, format_output

# Initialize console
console = Console()

# Create the module app
app = typer.Typer(
    name="module",
    help="Manage blockchain modules",
    no_args_is_help=True,
)


@app.command("list")
def list_modules():
    """
    List all available modules on the blockchain.
    
    This command queries the blockchain for all available modules
    and displays them in a list.
    """
    try:
        # Get client
        client = get_client()
        
        # Query modules
        modules = client.list_modules()
        
        # Format and display the result
        if get_global_context().json_output:
            format_output({"modules": modules}, "Available Modules")
        else:
            format_output(modules, "Available Modules")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("info")
def module_info(
    module_name: str = typer.Argument(..., help="The name of the module to query")
):
    """
    Get information about a specific module.
    
    This command queries the blockchain for information about the specified module
    and displays details such as storage items, calls, events, and errors.
    """
    try:
        # Get client
        client = get_client()
        
        # Query module info
        info = client.query_module_info(module_name)
        
        # Format and display the result
        format_output(info, f"Module Information: {module_name}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


# Add missing import
from src.cli.common import get_global_context
