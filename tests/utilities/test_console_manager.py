"""
Tests for the ConsoleManager class.
"""

import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import logging
import json
from pathlib import Path

import pytest
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

from src.utilities.console_manager import ConsoleManager, OutputFormat


class TestConsoleManager(unittest.TestCase):
    """Test cases for the ConsoleManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a string buffer to capture console output
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        
        # Patch sys.stdout and sys.stderr
        self.stdout_patch = patch('sys.stdout', self.stdout)
        self.stderr_patch = patch('sys.stderr', self.stderr)
        self.stdout_patch.start()
        self.stderr_patch.start()
        
        # Get a fresh instance of ConsoleManager for each test
        ConsoleManager._instances.clear()
        self.console_manager = ConsoleManager()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.stdout_patch.stop()
        self.stderr_patch.stop()
    
    def test_singleton_instance(self):
        """Test that ConsoleManager is a singleton."""
        console_manager1 = ConsoleManager()
        console_manager2 = ConsoleManager()
        self.assertIs(console_manager1, console_manager2)
    
    def test_print_text(self):
        """Test printing text to the console."""
        self.console_manager.print("Hello, world!")
        output = self.stdout.getvalue().strip()
        self.assertIn("Hello, world!", output)
    
    def test_print_json(self):
        """Test printing JSON to the console."""
        data = {"name": "John", "age": 30}
        self.console_manager.print_json(data)
        output = self.stdout.getvalue().strip()
        # Parse the output as JSON and compare
        parsed_output = json.loads(output)
        self.assertEqual(parsed_output, data)
    
    def test_print_table(self):
        """Test printing a table to the console."""
        headers = ["Name", "Age"]
        rows = [["John", "30"], ["Jane", "25"]]
        self.console_manager.print_table(headers, rows, title="People")
        output = self.stdout.getvalue().strip()
        # Check for table elements in the output
        self.assertIn("People", output)
        self.assertIn("Name", output)
        self.assertIn("Age", output)
        self.assertIn("John", output)
        self.assertIn("30", output)
    
    def test_print_error(self):
        """Test printing an error to the console."""
        self.console_manager.print_error("An error occurred")
        output = self.stderr.getvalue().strip()
        self.assertIn("An error occurred", output)
    
    def test_print_warning(self):
        """Test printing a warning to the console."""
        self.console_manager.print_warning("This is a warning")
        output = self.stderr.getvalue().strip()
        self.assertIn("This is a warning", output)
    
    def test_print_success(self):
        """Test printing a success message to the console."""
        self.console_manager.print_success("Operation successful")
        output = self.stdout.getvalue().strip()
        self.assertIn("Operation successful", output)
    
    def test_print_info(self):
        """Test printing an info message to the console."""
        self.console_manager.print_info("This is information")
        output = self.stdout.getvalue().strip()
        self.assertIn("This is information", output)
    
    def test_output_format(self):
        """Test setting and getting the output format."""
        self.console_manager.set_output_format(OutputFormat.JSON)
        self.assertEqual(self.console_manager.get_output_format(), OutputFormat.JSON)
        
        # Test that data is printed in JSON format
        data = {"name": "John", "age": 30}
        self.console_manager.print(data)
        output = self.stdout.getvalue().strip()
        parsed_output = json.loads(output)
        self.assertEqual(parsed_output, data)
    
    def test_progress_bar(self):
        """Test creating and updating a progress bar."""
        with patch.object(Console, 'print') as mock_print:
            with self.console_manager.progress_bar(total=100, description="Processing") as progress:
                for i in range(100):
                    progress.update(1)
            
            # Verify that the progress bar was created and updated
            mock_print.assert_called()
    
    def test_logging_integration(self):
        """Test integration with Python's logging module."""
        # Set up a logger with RichHandler
        with patch.object(ConsoleManager, '_setup_rich_handler') as mock_setup:
            self.console_manager.setup_logging(level=logging.INFO)
            mock_setup.assert_called_once()
    
    def test_exception_formatting(self):
        """Test formatting exceptions."""
        try:
            raise ValueError("This is a test exception")
        except ValueError as e:
            formatted = self.console_manager.format_exception(e)
            self.assertIn("ValueError", formatted)
            self.assertIn("This is a test exception", formatted)
    
    def test_spinner(self):
        """Test creating and using a spinner."""
        with patch.object(Console, 'print') as mock_print:
            with self.console_manager.spinner(text="Loading..."):
                # Simulate some work
                pass
            
            # Verify that the spinner was created and used
            mock_print.assert_called()


if __name__ == "__main__":
    unittest.main()
