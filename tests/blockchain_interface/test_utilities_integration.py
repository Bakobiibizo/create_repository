"""
Tests for the integration of blockchain interface with utilities component.
"""

import unittest
from unittest.mock import patch, MagicMock
import pytest
import os

from src.utilities.environment_manager import EnvironmentManager
from blockchain_interface.client import SubstrateClient
from blockchain_interface.connection import ConnectionManager


class TestUtilitiesIntegration(unittest.TestCase):
    """Test cases for the integration of blockchain interface with utilities component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_url = "ws://localhost:9944"
        
        # Set environment variables directly
        os.environ["BLOCKCHAIN_URL"] = self.valid_url
        os.environ["BLOCKCHAIN_RETRY_ATTEMPTS"] = "3"
        os.environ["BLOCKCHAIN_RETRY_DELAY"] = "1.0"
        os.environ["BLOCKCHAIN_MAX_CONNECTIONS"] = "5"
        os.environ["BLOCKCHAIN_IDLE_TIMEOUT"] = "300.0"
        os.environ["BLOCKCHAIN_HEARTBEAT_INTERVAL"] = "30.0"
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up environment variables
        for var in ["BLOCKCHAIN_URL", "BLOCKCHAIN_RETRY_ATTEMPTS", "BLOCKCHAIN_RETRY_DELAY", 
                  "BLOCKCHAIN_MAX_CONNECTIONS", "BLOCKCHAIN_IDLE_TIMEOUT", "BLOCKCHAIN_HEARTBEAT_INTERVAL"]:
            if var in os.environ:
                del os.environ[var]
    
    def test_client_uses_environment_manager(self):
        """Test that the client uses the Environment Manager for configuration."""
        # Initialize client without explicit URL
        client = SubstrateClient()
        
        # Verify that the client used the environment variables
        self.assertEqual(client.url, self.valid_url)
    
    def test_client_uses_environment_manager_for_retry_params(self):
        """Test that the client uses the Environment Manager for retry parameters."""
        # Initialize client without explicit retry parameters
        client = SubstrateClient()
        
        # Verify that the client used the environment variables for retry parameters
        self.assertEqual(client.retry_attempts, 3)
        self.assertEqual(client.retry_delay, 1.0)
    
    def test_connection_manager_uses_environment_manager(self):
        """Test that the connection manager uses the Environment Manager for configuration."""
        # Initialize connection manager without explicit URL
        manager = ConnectionManager()
        
        # Verify that the manager used the environment variables
        self.assertEqual(manager.url, self.valid_url)
    
    def test_connection_manager_uses_environment_manager_for_params(self):
        """Test that the connection manager uses the Environment Manager for parameters."""
        # Initialize connection manager without explicit parameters
        manager = ConnectionManager()
        
        # Verify that the manager used the environment variables for parameters
        self.assertEqual(manager.max_connections, 5)
        self.assertEqual(manager.idle_timeout, 300.0)
        self.assertEqual(manager.heartbeat_interval, 30.0)


if __name__ == "__main__":
    unittest.main()
