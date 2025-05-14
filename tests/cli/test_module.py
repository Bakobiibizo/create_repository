"""
Tests for the module commands in the ComAI Client CLI.

This module contains tests for the module command group, which includes
commands for listing and querying blockchain modules.
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

# Import the CLI app
from src.cli.root import app

# Initialize the test runner
runner = CliRunner()


@pytest.fixture
def mock_client():
    """Create a mock CommuneClient for testing."""
    with patch("src.cli.commands.module.get_client") as mock_get_client:
        client = MagicMock()
        mock_get_client.return_value = client
        yield client


class TestModuleCommands:
    """Test suite for module commands."""

    def test_list_modules_command(self, mock_client):
        """Test the list modules command."""
        # Mock the list_modules method to return test modules
        mock_client.list_modules.return_value = [
            "System",
            "Balances",
            "Staking",
            "Subnet",
            "Validator"
        ]

        # Run the command
        result = runner.invoke(app, ["module", "list"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the client method was called
        mock_client.list_modules.assert_called_once()
        
        # Check that the output contains the expected modules
        assert "System" in result.stdout
        assert "Balances" in result.stdout
        assert "Subnet" in result.stdout

    def test_list_modules_json_output(self, mock_client):
        """Test the list modules command with JSON output."""
        # Mock the list_modules method to return test modules
        mock_client.list_modules.return_value = [
            "System",
            "Balances",
            "Staking",
            "Subnet",
            "Validator"
        ]

        # Run the command with JSON output flag
        result = runner.invoke(app, ["--json", "module", "list"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the output is valid JSON and contains the expected data
        import json
        output = json.loads(result.stdout)
        assert "System" in output["modules"]
        assert "Balances" in output["modules"]
        assert "Subnet" in output["modules"]

    def test_module_info_command(self, mock_client):
        """Test the module info command."""
        # Mock the query_module_info method to return test module info
        mock_client.query_module_info.return_value = {
            "name": "Balances",
            "storage_items": ["Account", "TotalIssuance", "Locks"],
            "calls": ["transfer", "force_transfer", "transfer_keep_alive"],
            "events": ["Transfer", "BalanceSet", "Deposit"],
            "errors": ["InsufficientBalance", "ExistentialDeposit", "KeepAlive"]
        }

        # Run the command
        result = runner.invoke(app, ["module", "info", "Balances"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the client method was called with the correct arguments
        mock_client.query_module_info.assert_called_once_with("Balances")
        
        # Check that the output contains the expected module information
        assert "Balances" in result.stdout
        assert "transfer" in result.stdout
        assert "InsufficientBalance" in result.stdout

    def test_module_info_json_output(self, mock_client):
        """Test the module info command with JSON output."""
        # Mock the query_module_info method to return test module info
        mock_client.query_module_info.return_value = {
            "name": "Balances",
            "storage_items": ["Account", "TotalIssuance", "Locks"],
            "calls": ["transfer", "force_transfer", "transfer_keep_alive"],
            "events": ["Transfer", "BalanceSet", "Deposit"],
            "errors": ["InsufficientBalance", "ExistentialDeposit", "KeepAlive"]
        }

        # Run the command with JSON output flag
        result = runner.invoke(app, ["--json", "module", "info", "Balances"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the output is valid JSON and contains the expected data
        import json
        output = json.loads(result.stdout)
        assert output["name"] == "Balances"
        assert "transfer" in output["calls"]
        assert "InsufficientBalance" in output["errors"]

    def test_module_info_invalid_module(self, mock_client):
        """Test the module info command with an invalid module name."""
        # Mock the query_module_info method to raise an exception for invalid module
        mock_client.query_module_info.side_effect = ValueError("Module not found")

        # Run the command with an invalid module name
        result = runner.invoke(app, ["module", "info", "InvalidModule"])

        # Check that the command failed
        assert result.exit_code == 1
        
        # Check that the error message is displayed
        assert "Module not found" in result.stdout
