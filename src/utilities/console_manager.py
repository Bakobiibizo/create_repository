"""
Console Manager for ComAI Client.

This module provides a centralized console management system for the ComAI Client,
ensuring consistent output formatting, error handling, and logging across the application.
It leverages the rich library to provide beautiful and informative console output.
"""

import sys
import json
import logging
import traceback
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union, TextIO, Iterator, cast

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.logging import RichHandler
from rich.traceback import Traceback
from rich.spinner import Spinner
from rich.style import Style
from rich.theme import Theme

from .singleton import Singleton


class OutputFormat(Enum):
    """Enum representing different output formats."""
    TEXT = auto()
    JSON = auto()
    TABLE = auto()


class ConsoleManager(metaclass=Singleton):
    """
    Centralized console management for the ComAI Client.
    
    This class provides methods for printing formatted output to the console,
    handling errors, and integrating with the logging system.
    
    Attributes:
        console: The rich console instance.
        error_console: The rich console instance for errors.
        output_format: The current output format.
    """
    
    def __init__(self) -> None:
        """Initialize the ConsoleManager with default settings."""
        # Define custom theme
        theme = Theme({
            "info": "cyan",
            "warning": "yellow",
            "error": "bold red",
            "success": "bold green",
        })
        
        # Create console instances
        self.console = Console(theme=theme)
        self.error_console = Console(stderr=True, theme=theme)
        
        # Set default output format
        self._output_format = OutputFormat.TEXT
        
        # Initialize logger
        self._logger = None
    
    def print(self, message: Any, **kwargs: Any) -> None:
        """
        Print a message to the console.
        
        Args:
            message: The message to print.
            **kwargs: Additional arguments to pass to the console.print method.
        """
        if self._output_format == OutputFormat.JSON and not isinstance(message, str):
            self.print_json(message)
        else:
            self.console.print(message, **kwargs)
    
    def print_json(self, data: Any, indent: int = 2, **kwargs: Any) -> None:
        """
        Print data as JSON to the console.
        
        Args:
            data: The data to print as JSON.
            indent: The indentation level for the JSON output.
            **kwargs: Additional arguments to pass to the console.print method.
        """
        json_str = json.dumps(data, indent=indent)
        self.console.print(json_str, **kwargs)
    
    def print_table(self, headers: List[str], rows: List[List[Any]], title: Optional[str] = None, **kwargs: Any) -> None:
        """
        Print data as a table to the console.
        
        Args:
            headers: The table headers.
            rows: The table rows.
            title: Optional title for the table.
            **kwargs: Additional arguments to pass to the console.print method.
        """
        table = Table(title=title)
        
        # Add headers
        for header in headers:
            table.add_column(str(header))
        
        # Add rows
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        
        self.console.print(table, **kwargs)
    
    def print_error(self, message: str, **kwargs: Any) -> None:
        """
        Print an error message to the console.
        
        Args:
            message: The error message to print.
            **kwargs: Additional arguments to pass to the console.print method.
        """
        self.error_console.print(f"[error]Error:[/error] {message}", **kwargs)
    
    def print_warning(self, message: str, **kwargs: Any) -> None:
        """
        Print a warning message to the console.
        
        Args:
            message: The warning message to print.
            **kwargs: Additional arguments to pass to the console.print method.
        """
        self.error_console.print(f"[warning]Warning:[/warning] {message}", **kwargs)
    
    def print_success(self, message: str, **kwargs: Any) -> None:
        """
        Print a success message to the console.
        
        Args:
            message: The success message to print.
            **kwargs: Additional arguments to pass to the console.print method.
        """
        self.console.print(f"[success]Success:[/success] {message}", **kwargs)
    
    def print_info(self, message: str, **kwargs: Any) -> None:
        """
        Print an info message to the console.
        
        Args:
            message: The info message to print.
            **kwargs: Additional arguments to pass to the console.print method.
        """
        self.console.print(f"[info]Info:[/info] {message}", **kwargs)
    
    def set_output_format(self, format: OutputFormat) -> None:
        """
        Set the output format.
        
        Args:
            format: The output format to use.
        """
        self._output_format = format
    
    def get_output_format(self) -> OutputFormat:
        """
        Get the current output format.
        
        Returns:
            The current output format.
        """
        return self._output_format
    
    def progress_bar(self, total: int, description: str = "Progress", **kwargs: Any) -> Progress:
        """
        Create a progress bar.
        
        Args:
            total: The total number of steps.
            description: The description of the progress bar.
            **kwargs: Additional arguments to pass to the Progress constructor.
            
        Returns:
            A Progress instance.
        """
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console,
            **kwargs
        )
        task_id = progress.add_task(description, total=total)
        
        # Return a wrapper that updates the specific task
        class ProgressWrapper:
            def __init__(self, progress, task_id):
                self.progress = progress
                self.task_id = task_id
            
            def __enter__(self):
                self.progress.start()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.progress.stop()
            
            def update(self, advance=1):
                self.progress.update(self.task_id, advance=advance)
        
        return ProgressWrapper(progress, task_id)
    
    def spinner(self, text: str = "Loading...", **kwargs: Any) -> "SpinnerContext":
        """
        Create a spinner.
        
        Args:
            text: The text to display next to the spinner.
            **kwargs: Additional arguments to pass to the Spinner constructor.
            
        Returns:
            A context manager that displays a spinner while executing code.
        """
        class SpinnerContext:
            def __init__(self, console, text, **kwargs):
                self.console = console
                self.text = text
                self.kwargs = kwargs
                self.spinner = None
            
            def __enter__(self):
                self.spinner = Spinner("dots", text=self.text, **self.kwargs)
                self.console.print(self.spinner)
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    self.console.print(f"{self.text} [success]Done![/success]")
                else:
                    self.console.print(f"{self.text} [error]Failed![/error]")
        
        return SpinnerContext(self.console, text, **kwargs)
    
    def format_exception(self, exception: Exception) -> str:
        """
        Format an exception for display.
        
        Args:
            exception: The exception to format.
            
        Returns:
            A formatted string representation of the exception.
        """
        # Create a simple formatted string representation of the exception
        formatted = f"[bold red]{type(exception).__name__}:[/bold red] {str(exception)}"
        
        # Add traceback information if available
        if exception.__traceback__:
            tb_lines = traceback.format_tb(exception.__traceback__)
            formatted += "\n\nTraceback (most recent call last):\n"
            formatted += "".join(tb_lines)
        
        # Return the formatted string
        return formatted
    
    def setup_logging(self, level: int = logging.INFO, format: str = "%(message)s", **kwargs: Any) -> logging.Logger:
        """
        Set up logging with RichHandler.
        
        Args:
            level: The logging level.
            format: The log format.
            **kwargs: Additional arguments to pass to the RichHandler constructor.
            
        Returns:
            The configured logger.
        """
        if self._logger is None:
            # Create a RichHandler
            handler = self._setup_rich_handler(level, **kwargs)
            
            # Configure the root logger
            logging.basicConfig(
                level=level,
                format=format,
                datefmt="[%X]",
                handlers=[handler]
            )
            
            # Get a logger for this module
            self._logger = logging.getLogger("com_ai")
        
        return self._logger
    
    def _setup_rich_handler(self, level: int = logging.INFO, **kwargs: Any) -> RichHandler:
        """
        Set up a RichHandler for logging.
        
        Args:
            level: The logging level.
            **kwargs: Additional arguments to pass to the RichHandler constructor.
            
        Returns:
            A configured RichHandler.
        """
        return RichHandler(
            level=level,
            console=self.console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            **kwargs
        )


def get_console_manager() -> ConsoleManager:
    """
    Get the singleton instance of the ConsoleManager.
    
    Returns:
        The ConsoleManager instance.
    """
    return ConsoleManager()
