"""
Tests for the network commands in the ComAI Client CLI.

This module contains tests for the network command group, which includes
commands for querying network status and information.
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
    with patch("src.cli.commands.network.get_client") as mock_get_client:
        client = MagicMock()
        mock_get_client.return_value = client
        yield client


class TestNetworkCommands:
    """Test suite for network commands."""

    def test_status_command(self, mock_client):
        """Test the network status command."""
        # Mock the query_network_status method to return test status
        mock_client.query_network_status.return_value = {
            "health": "healthy",
            "peers": 5,
            "is_syncing": False,
            "best_block": 12345,
            "finalized_block": 12340
        }

        # Run the command
        result = runner.invoke(app, ["network", "status"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the client method was called
        mock_client.query_network_status.assert_called_once()
        
        # Check that the output contains the expected status information
        assert "healthy" in result.stdout
        assert "5" in result.stdout
        assert "12345" in result.stdout

    def test_status_command_json_output(self, mock_client):
        """Test the network status command with JSON output."""
        # Mock the query_network_status method to return test status
        mock_client.query_network_status.return_value = {
            "health": "healthy",
            "peers": 5,
            "is_syncing": False,
            "best_block": 12345,
            "finalized_block": 12340
        }

        # Run the command with JSON output flag
        result = runner.invoke(app, ["--json", "network", "status"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the output is valid JSON and contains the expected data
        import json
        output = json.loads(result.stdout)
        assert output["health"] == "healthy"
        assert output["peers"] == 5
        assert output["best_block"] == 12345

    def test_info_command(self, mock_client):
        """Test the network info command."""
        # Mock the query_system_chain and query_system_version methods
        mock_client.query_system_chain.return_value = "CommuneAI"
        mock_client.query_system_version.return_value = "1.0.0"
        mock_client.query_system_properties.return_value = {
            "ss58Format": 42,
            "tokenDecimals": 12,
            "tokenSymbol": "COM"
        }

        # Run the command
        result = runner.invoke(app, ["network", "info"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the client methods were called
        mock_client.query_system_chain.assert_called_once()
        mock_client.query_system_version.assert_called_once()
        mock_client.query_system_properties.assert_called_once()
        
        # Check that the output contains the expected information
        assert "CommuneAI" in result.stdout
        assert "1.0.0" in result.stdout
        assert "COM" in result.stdout

    def test_info_command_json_output(self, mock_client):
        """Test the network info command with JSON output."""
        # Mock the query_system_chain and query_system_version methods
        mock_client.query_system_chain.return_value = "CommuneAI"
        mock_client.query_system_version.return_value = "1.0.0"
        mock_client.query_system_properties.return_value = {
            "ss58Format": 42,
            "tokenDecimals": 12,
            "tokenSymbol": "COM"
        }

        # Run the command with JSON output flag
        result = runner.invoke(app, ["--json", "network", "info"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the output is valid JSON and contains the expected data
        import json
        output = json.loads(result.stdout)
        assert output["chain"] == "CommuneAI"
        assert output["version"] == "1.0.0"
        assert output["properties"]["tokenSymbol"] == "COM"
