"""
Miscellaneous commands for the ComAI Client CLI.

This module provides miscellaneous commands that don't fit into other categories.
"""

import typer
from typing import Optional
from rich.console import Console
import pkg_resources

from src.cli.common import get_client, format_output

# Initialize console
console = Console()

# Create the misc app
app = typer.Typer(
    name="misc",
    help="Miscellaneous commands",
    no_args_is_help=True,
)


@app.command("version")
def version():
    """
    Display the version of the ComAI Client.
    
    This command displays the current version of the ComAI Client CLI.
    """
    try:
        # Get version from package resources
        try:
            version = pkg_resources.get_distribution("comai-client").version
        except pkg_resources.DistributionNotFound:
            version = "development"
        
        # Display version
        console.print(f"[bold]ComAI Client[/bold] version [cyan]{version}[/cyan]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("config")
def config():
    """
    Display the current configuration.
    
    This command displays the current configuration settings for the ComAI Client.
    """
    try:
        from src.utilities.environment_manager import get_environment_manager
        
        env_manager = get_environment_manager()
        
        # Get configuration
        config = {
            "node_url": env_manager.get_var("COMAI_NODE_URL", "ws://127.0.0.1:9944"),
            "keys_dir": env_manager.get_var("COMAI_KEYS_DIR", "~/.comai/keys"),
            "debug": env_manager.get_var_as_bool("COMAI_DEBUG", False),
            "log_level": env_manager.get_var("COMAI_LOG_LEVEL", "INFO")
        }
        
        # Format and display the result
        format_output(config, "Current Configuration")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)
