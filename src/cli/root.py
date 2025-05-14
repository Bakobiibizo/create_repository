"""
Root command group for the ComAI Client CLI.

This module defines the root command group and registers all subcommand groups.
It serves as the main entry point for the CLI application.
"""

import typer
from typing import Optional
from rich.console import Console

from src.cli.commands import (
    balance,
    network,
    module,
    key,
    subnet,
    misc
)

# Initialize rich console
console = Console()

# Create the root app
app = typer.Typer(
    name="comai",
    help="ComAI Client - Command-line interface for interacting with the CommuneAI blockchain",
    no_args_is_help=True,
)

# Register command groups
app.add_typer(balance.app, name="balance", help="Manage account balances")
app.add_typer(network.app, name="network", help="Interact with the blockchain network")
app.add_typer(module.app, name="module", help="Manage blockchain modules")
app.add_typer(key.app, name="key", help="Manage cryptographic keys")
app.add_typer(subnet.app, name="subnet", help="Manage subnets")
app.add_typer(misc.app, name="misc", help="Miscellaneous commands")

@app.callback()
def callback(
    verbose: Optional[bool] = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    json_output: Optional[bool] = typer.Option(
        False, "--json", "-j", help="Output in JSON format"
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
):
    """
    ComAI Client - Command-line interface for interacting with the CommuneAI blockchain.
    
    This CLI provides tools for managing accounts, querying blockchain data,
    and interacting with the CommuneAI network.
    """
    # Store global options in a context object that can be accessed by subcommands
    from src.cli.common import GlobalContext
    
    ctx = GlobalContext()
    ctx.verbose = verbose
    ctx.json_output = json_output
    ctx.config_path = config
    
    # Set the context as a global variable
    import src.cli.common as common
    common.global_context = ctx
