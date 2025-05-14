"""
Example demonstrating the use of the ConsoleManager.

This script shows how to use the ConsoleManager to display formatted output,
handle errors, and integrate with the logging system.
"""

import sys
import logging
from typing import Dict, List, Any

from src.utilities import get_console_manager, OutputFormat


def main() -> None:
    """Run the ConsoleManager example."""
    # Get the console manager instance
    console = get_console_manager()
    
    # Set up logging
    logger = console.setup_logging(level=logging.INFO)
    
    # Print a welcome message
    console.print("[bold blue]ConsoleManager Example[/bold blue]")
    console.print("This example demonstrates the various features of the ConsoleManager.")
    
    # Print different message types
    console.print_info("This is an informational message.")
    console.print_success("This is a success message.")
    console.print_warning("This is a warning message.")
    console.print_error("This is an error message.")
    
    # Print JSON data
    data = {
        "name": "ComAI Client",
        "version": "0.1.0",
        "components": ["CLI", "Blockchain Interface", "REST API", "MCP Server"],
        "status": "In Development"
    }
    console.print("\n[bold]JSON Output:[/bold]")
    console.print_json(data)
    
    # Print a table
    console.print("\n[bold]Table Output:[/bold]")
    headers = ["Component", "Status", "Priority"]
    rows = [
        ["CLI", "In Progress", "High"],
        ["Blockchain Interface", "Completed", "High"],
        ["REST API", "Planned", "Medium"],
        ["MCP Server", "Planned", "Low"]
    ]
    console.print_table(headers, rows, title="ComAI Client Components")
    
    # Demonstrate progress bar
    console.print("\n[bold]Progress Bar Example:[/bold]")
    with console.progress_bar(total=100, description="Processing") as progress:
        for i in range(10):
            # Simulate some work
            import time
            time.sleep(0.1)
            progress.update(10)
    
    # Demonstrate spinner
    console.print("\n[bold]Spinner Example:[/bold]")
    with console.spinner(text="Loading data"):
        # Simulate some work
        import time
        time.sleep(2)
    
    # Demonstrate exception handling
    console.print("\n[bold]Exception Handling Example:[/bold]")
    try:
        # Simulate an exception
        raise ValueError("This is a test exception")
    except Exception as e:
        formatted = console.format_exception(e)
        console.print(formatted)
    
    # Demonstrate logging integration
    console.print("\n[bold]Logging Integration Example:[/bold]")
    logger.debug("This is a debug message (not shown with INFO level)")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Demonstrate output format switching
    console.print("\n[bold]Output Format Switching Example:[/bold]")
    console.print("Current format: TEXT")
    
    console.set_output_format(OutputFormat.JSON)
    console.print("Switching to JSON format...")
    console.print(data)  # Will be printed as JSON
    
    console.set_output_format(OutputFormat.TEXT)
    console.print("Switching back to TEXT format...")
    console.print(data)  # Will be printed as string representation
    
    # Print a goodbye message
    console.print("\n[bold green]Example completed successfully![/bold green]")


if __name__ == "__main__":
    main()
