"""
Tests for the subnet commands in the ComAI Client CLI.

This module contains tests for the subnet command group, which includes
commands for listing and querying subnets.
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
    with patch("src.cli.commands.subnet.get_client") as mock_get_client:
        client = MagicMock()
        mock_get_client.return_value = client
        yield client


class TestSubnetCommands:
    """Test suite for subnet commands."""

    def test_list_subnets_command(self, mock_client):
        """Test the list subnets command."""
        # Mock the list_subnets method to return test subnets
        mock_client.list_subnets.return_value = [
            {
                "id": 1,
                "name": "main",
                "owner": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "stake": 1000000000000,
                "validators": 10
            },
            {
                "id": 2,
                "name": "compute",
                "owner": "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
                "stake": 500000000000,
                "validators": 5
            }
        ]

        # Run the command
        result = runner.invoke(app, ["subnet", "list"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the client method was called
        mock_client.list_subnets.assert_called_once()
        
        # Check that the output contains the expected subnets
        assert "main" in result.stdout
        assert "compute" in result.stdout
        assert "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY" in result.stdout

    def test_list_subnets_json_output(self, mock_client):
        """Test the list subnets command with JSON output."""
        # Mock the list_subnets method to return test subnets
        mock_client.list_subnets.return_value = [
            {
                "id": 1,
                "name": "main",
                "owner": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "stake": 1000000000000,
                "validators": 10
            },
            {
                "id": 2,
                "name": "compute",
                "owner": "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
                "stake": 500000000000,
                "validators": 5
            }
        ]

        # Run the command with JSON output flag
        result = runner.invoke(app, ["--json", "subnet", "list"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the output is valid JSON and contains the expected data
        import json
        output = json.loads(result.stdout)
        assert len(output) == 2
        assert output[0]["name"] == "main"
        assert output[1]["name"] == "compute"

    def test_subnet_info_command(self, mock_client):
        """Test the subnet info command."""
        # Mock the query_subnet_info method to return test subnet info
        mock_client.query_subnet_info.return_value = {
            "id": 1,
            "name": "main",
            "owner": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            "stake": 1000000000000,
            "validators": [
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty"
            ],
            "modules": ["Balances", "Staking", "Subnet"],
            "created_at": 12345,
            "status": "active"
        }

        # Run the command
        result = runner.invoke(app, ["subnet", "info", "1"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the client method was called with the correct arguments
        mock_client.query_subnet_info.assert_called_once_with(1)
        
        # Check that the output contains the expected subnet information
        assert "main" in result.stdout
        assert "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY" in result.stdout
        assert "active" in result.stdout

    def test_subnet_info_json_output(self, mock_client):
        """Test the subnet info command with JSON output."""
        # Mock the query_subnet_info method to return test subnet info
        mock_client.query_subnet_info.return_value = {
            "id": 1,
            "name": "main",
            "owner": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            "stake": 1000000000000,
            "validators": [
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty"
            ],
            "modules": ["Balances", "Staking", "Subnet"],
            "created_at": 12345,
            "status": "active"
        }

        # Run the command with JSON output flag
        result = runner.invoke(app, ["--json", "subnet", "info", "1"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the output is valid JSON and contains the expected data
        import json
        output = json.loads(result.stdout)
        assert output["name"] == "main"
        assert output["status"] == "active"
        assert len(output["validators"]) == 2

    def test_subnet_info_invalid_id(self, mock_client):
        """Test the subnet info command with an invalid subnet ID."""
        # Mock the query_subnet_info method to raise an exception for invalid subnet ID
        mock_client.query_subnet_info.side_effect = ValueError("Subnet not found")

        # Run the command with an invalid subnet ID
        result = runner.invoke(app, ["subnet", "info", "999"])

        # Check that the command failed
        assert result.exit_code == 1
        
        # Check that the error message is displayed
        assert "Subnet not found" in result.stdout
