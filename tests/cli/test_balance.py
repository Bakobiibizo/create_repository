"""
Tests for the balance commands in the ComAI Client CLI.

This module contains tests for the balance command group, which includes
commands for querying account balances and transferring tokens.
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
    with patch("src.cli.commands.balance.get_client") as mock_get_client:
        client = MagicMock()
        mock_get_client.return_value = client
        yield client


class TestBalanceCommands:
    """Test suite for balance commands."""

    def test_get_balance_command(self, mock_client):
        """Test the get balance command."""
        # Mock the query_balance method to return a test balance
        mock_client.query_balance.return_value = {
            "free": 1000000000000,
            "reserved": 0,
            "frozen": 0,
            "flags": 0
        }

        # Run the command
        result = runner.invoke(app, ["balance", "get", "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the client method was called with the correct arguments
        mock_client.query_balance.assert_called_once_with("5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY")
        
        # Check that the output contains the expected balance information
        assert "1000000000000" in result.stdout
        assert "Free" in result.stdout

    def test_get_balance_json_output(self, mock_client):
        """Test the get balance command with JSON output."""
        # Mock the query_balance method to return a test balance
        mock_client.query_balance.return_value = {
            "free": 1000000000000,
            "reserved": 0,
            "frozen": 0,
            "flags": 0
        }

        # Run the command with JSON output flag
        result = runner.invoke(app, ["--json", "balance", "get", "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the output is valid JSON and contains the expected data
        import json
        output = json.loads(result.stdout)
        assert output["free"] == 1000000000000
        assert output["reserved"] == 0

    def test_get_balance_invalid_address(self, mock_client):
        """Test the get balance command with an invalid address."""
        # Mock the query_balance method to raise an exception for invalid address
        mock_client.query_balance.side_effect = ValueError("Invalid address format")

        # Run the command with an invalid address
        result = runner.invoke(app, ["balance", "get", "invalid_address"])

        # Check that the command failed
        assert result.exit_code == 1
        
        # Check that the error message is displayed
        assert "Invalid address format" in result.stdout

    def test_transfer_command(self, mock_client):
        """Test the transfer command."""
        # Mock the transfer_tokens method
        mock_client.transfer_tokens.return_value = {
            "hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "block": 12345
        }

        # Run the command
        result = runner.invoke(
            app, 
            [
                "balance", "transfer", 
                "--from", "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "--to", "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
                "--amount", "100",
                "--wait"
            ]
        )

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the client method was called with the correct arguments
        mock_client.transfer_tokens.assert_called_once_with(
            from_address="5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            to_address="5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
            amount=100,
            wait_for_inclusion=True
        )
        
        # Check that the output contains the transaction hash
        assert "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" in result.stdout
        assert "Transaction successful" in result.stdout

    def test_transfer_command_no_wait(self, mock_client):
        """Test the transfer command without waiting for inclusion."""
        # Mock the transfer_tokens method
        mock_client.transfer_tokens.return_value = {
            "hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "block": None
        }

        # Run the command without the wait flag
        result = runner.invoke(
            app, 
            [
                "balance", "transfer", 
                "--from", "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "--to", "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
                "--amount", "100"
            ]
        )

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the client method was called with the correct arguments
        mock_client.transfer_tokens.assert_called_once_with(
            from_address="5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            to_address="5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
            amount=100,
            wait_for_inclusion=False
        )
        
        # Check that the output contains the transaction hash
        assert "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" in result.stdout
        assert "Transaction submitted" in result.stdout

    def test_transfer_command_insufficient_funds(self, mock_client):
        """Test the transfer command with insufficient funds."""
        # Mock the transfer_tokens method to raise an exception for insufficient funds
        mock_client.transfer_tokens.side_effect = ValueError("Insufficient funds")

        # Run the command
        result = runner.invoke(
            app, 
            [
                "balance", "transfer", 
                "--from", "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "--to", "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
                "--amount", "999999999999999"
            ]
        )

        # Check that the command failed
        assert result.exit_code == 1
        
        # Check that the error message is displayed
        assert "Insufficient funds" in result.stdout
