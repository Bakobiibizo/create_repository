"""
Balance commands for the ComAI Client CLI.

This module provides commands for querying account balances and transferring tokens.
"""

import typer
from typing import Optional
from rich.console import Console

from src.cli.common import get_client, format_output, format_balance

# Initialize console
console = Console()

# Create the balance app
app = typer.Typer(
    name="balance",
    help="Manage account balances",
    no_args_is_help=True,
)


@app.command("get")
def get_balance(
    address: str = typer.Argument(..., help="The account address to query")
):
    """
    Get the balance for an account.
    
    This command queries the blockchain for the balance of the specified account
    and displays the result.
    """
    try:
        # Get client
        client = get_client()
        
        # Query balance
        balance = client.query_balance(address)
        
        # Format and display the result
        from src.cli.common import get_global_context
        
        if get_global_context().json_output:
            # For JSON output, use the raw balance object
            format_output(balance)
        else:
            # For human-readable output, format the balance
            formatted_balance = format_balance(balance)
            format_output(formatted_balance, f"Balance for {address}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("transfer")
def transfer(
    from_address: str = typer.Option(
        ..., "--from", help="The sender's account address"
    ),
    to_address: str = typer.Option(
        ..., "--to", help="The recipient's account address"
    ),
    amount: float = typer.Option(
        ..., "--amount", help="The amount to transfer"
    ),
    wait: bool = typer.Option(
        False, "--wait", help="Wait for the transaction to be included in a block"
    ),
):
    """
    Transfer tokens between accounts.
    
    This command transfers tokens from one account to another and
    optionally waits for the transaction to be included in a block.
    """
    try:
        # Get client
        client = get_client()
        
        # Transfer tokens
        result = client.transfer_tokens(
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            wait_for_inclusion=wait
        )
        
        # Format and display the result
        if wait:
            console.print(f"[bold green]Transaction successful[/bold green]")
            console.print(f"Transaction hash: {result['hash']}")
            console.print(f"Included in block: {result['block']}")
        else:
            console.print(f"[bold yellow]Transaction submitted[/bold yellow]")
            console.print(f"Transaction hash: {result['hash']}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)
