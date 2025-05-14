#!/usr/bin/env python3
"""
ComAI Client CLI Entry Point.

This module serves as the main entry point for the ComAI Client CLI application.
It initializes the command-line interface and routes commands to appropriate handlers.
"""

import sys
import typer
from rich.console import Console
from rich.traceback import install

from src.cli.root import app
from src.utilities.environment_manager import get_environment_manager

# Install rich traceback handler
install(show_locals=False)

# Initialize rich console
console = Console()

def main():
    """
    Main entry point for the ComAI Client CLI.
    
    This function initializes the CLI application, sets up global options and configuration,
    and handles global error conditions.
    
    Returns:
        int: Exit code (0 for success, non-zero for error).
    """
    try:
        # Get environment manager
        env_manager = get_environment_manager()
        
        # Set up global options from environment variables
        debug_mode = env_manager.get_var_as_bool("COMAI_DEBUG", False)
        
        # Run the application
        app()
        return 0
    except Exception as e:
        if env_manager.get_var_as_bool("COMAI_DEBUG", False):
            console.print_exception()
        else:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
