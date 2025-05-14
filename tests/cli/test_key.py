"""
Tests for the key commands in the ComAI Client CLI.

This module contains tests for the key command group, which includes
commands for managing cryptographic keys.
"""

import pytest
import os
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock, mock_open

# Import the CLI app
from src.cli.root import app

# Initialize the test runner
runner = CliRunner()


@pytest.fixture
def mock_key_manager():
    """Create a mock KeyManager for testing."""
    with patch("src.cli.commands.key.KeyManager") as mock_key_manager_class:
        key_manager = MagicMock()
        mock_key_manager_class.return_value = key_manager
        yield key_manager


class TestKeyCommands:
    """Test suite for key commands."""

    def test_list_keys_command(self, mock_key_manager):
        """Test the list keys command."""
        # Mock the list_keys method to return test keys
        mock_key_manager.list_keys.return_value = [
            {
                "name": "default",
                "address": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "type": "sr25519"
            },
            {
                "name": "validator",
                "address": "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
                "type": "ed25519"
            }
        ]

        # Run the command
        result = runner.invoke(app, ["key", "list"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the key manager method was called
        mock_key_manager.list_keys.assert_called_once()
        
        # Check that the output contains the expected keys
        assert "default" in result.stdout
        assert "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY" in result.stdout
        assert "validator" in result.stdout

    def test_list_keys_json_output(self, mock_key_manager):
        """Test the list keys command with JSON output."""
        # Mock the list_keys method to return test keys
        mock_key_manager.list_keys.return_value = [
            {
                "name": "default",
                "address": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "type": "sr25519"
            },
            {
                "name": "validator",
                "address": "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
                "type": "ed25519"
            }
        ]

        # Run the command with JSON output flag
        result = runner.invoke(app, ["--json", "key", "list"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the output is valid JSON and contains the expected data
        import json
        output = json.loads(result.stdout)
        assert len(output) == 2
        assert output[0]["name"] == "default"
        assert output[1]["name"] == "validator"

    def test_generate_key_command(self, mock_key_manager):
        """Test the generate key command."""
        # Mock the generate_key method to return a test key
        mock_key_manager.generate_key.return_value = {
            "name": "new_key",
            "address": "5FLSigC9HGRKVhB9FiEo4Y3koPsNmBmLJbpXg2mp1hXcS59Y",
            "type": "sr25519",
            "mnemonic": "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12"
        }

        # Run the command
        result = runner.invoke(app, ["key", "generate", "new_key", "--type", "sr25519"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the key manager method was called with the correct arguments
        mock_key_manager.generate_key.assert_called_once_with("new_key", "sr25519")
        
        # Check that the output contains the expected key information
        assert "new_key" in result.stdout
        assert "5FLSigC9HGRKVhB9FiEo4Y3koPsNmBmLJbpXg2mp1hXcS59Y" in result.stdout
        assert "word1 word2 word3" in result.stdout

    def test_import_key_command(self, mock_key_manager):
        """Test the import key command."""
        # Mock the import_key method
        mock_key_manager.import_key.return_value = {
            "name": "imported_key",
            "address": "5FLSigC9HGRKVhB9FiEo4Y3koPsNmBmLJbpXg2mp1hXcS59Y",
            "type": "sr25519"
        }

        # Run the command
        result = runner.invoke(
            app, 
            ["key", "import", "imported_key", "--mnemonic", "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12", "--type", "sr25519"]
        )

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the key manager method was called with the correct arguments
        mock_key_manager.import_key.assert_called_once_with(
            "imported_key", 
            "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12", 
            "sr25519"
        )
        
        # Check that the output contains the expected key information
        assert "imported_key" in result.stdout
        assert "5FLSigC9HGRKVhB9FiEo4Y3koPsNmBmLJbpXg2mp1hXcS59Y" in result.stdout

    def test_export_key_command(self, mock_key_manager):
        """Test the export key command."""
        # Mock the export_key method
        mock_key_manager.export_key.return_value = {
            "name": "default",
            "address": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            "type": "sr25519",
            "mnemonic": "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12"
        }

        # Run the command
        result = runner.invoke(app, ["key", "export", "default"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the key manager method was called with the correct arguments
        mock_key_manager.export_key.assert_called_once_with("default")
        
        # Check that the output contains the expected key information
        assert "default" in result.stdout
        assert "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY" in result.stdout
        assert "word1 word2 word3" in result.stdout

    def test_delete_key_command(self, mock_key_manager):
        """Test the delete key command."""
        # Mock the delete_key method
        mock_key_manager.delete_key.return_value = True

        # Run the command
        result = runner.invoke(app, ["key", "delete", "default", "--yes"])

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the key manager method was called with the correct arguments
        mock_key_manager.delete_key.assert_called_once_with("default")
        
        # Check that the output contains the expected confirmation
        assert "deleted" in result.stdout.lower()

    def test_delete_key_command_with_confirmation(self, mock_key_manager):
        """Test the delete key command with confirmation."""
        # Mock the delete_key method
        mock_key_manager.delete_key.return_value = True

        # Run the command without the --yes flag, but simulate 'y' input
        result = runner.invoke(app, ["key", "delete", "default"], input="y\n")

        # Check that the command was successful
        assert result.exit_code == 0
        
        # Check that the key manager method was called with the correct arguments
        mock_key_manager.delete_key.assert_called_once_with("default")
        
        # Check that the output contains the expected confirmation
        assert "deleted" in result.stdout.lower()

    def test_delete_key_command_cancelled(self, mock_key_manager):
        """Test the delete key command cancelled by user."""
        # Run the command without the --yes flag, but simulate 'n' input
        result = runner.invoke(app, ["key", "delete", "default"], input="n\n")

        # Check that the command was cancelled
        assert result.exit_code == 0
        
        # Check that the key manager method was not called
        mock_key_manager.delete_key.assert_not_called()
        
        # Check that the output contains the expected cancellation message
        assert "cancelled" in result.stdout.lower()
