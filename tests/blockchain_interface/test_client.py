"""
Tests for the SubstrateClient class.
"""

import unittest
from unittest.mock import patch, MagicMock
import pytest
from urllib.parse import urlparse

# Import for mocking
from substrateinterface import SubstrateInterface

from blockchain_interface.client import SubstrateClient


class TestSubstrateClient(unittest.TestCase):
    """Test cases for the SubstrateClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_url = "ws://localhost:9944"
        self.invalid_url = "http://localhost:9944"
    
    def test_init_with_valid_url(self):
        """Test initialization with a valid WebSocket URL."""
        client = SubstrateClient(self.valid_url)
        self.assertEqual(client.url, self.valid_url)
        self.assertEqual(client.retry_attempts, 3)  # Default value
        self.assertEqual(client.retry_delay, 1.0)  # Default value
        self.assertIsNone(client.connection)
        self.assertFalse(client.connected)
    
    def test_init_with_invalid_url(self):
        """Test initialization with an invalid URL scheme."""
        with self.assertRaises(ValueError) as context:
            SubstrateClient(self.invalid_url)
        self.assertIn("Invalid URL scheme", str(context.exception))
    
    def test_init_with_custom_retry_params(self):
        """Test initialization with custom retry parameters."""
        retry_attempts = 5
        retry_delay = 2.0
        client = SubstrateClient(self.valid_url, retry_attempts=retry_attempts, retry_delay=retry_delay)
        self.assertEqual(client.retry_attempts, retry_attempts)
        self.assertEqual(client.retry_delay, retry_delay)
    
    @patch('blockchain_interface.client.SubstrateInterface')
    def test_connect_success(self, mock_substrate_interface):
        """Test successful connection to the blockchain."""
        # Setup mock
        mock_instance = MagicMock()
        mock_substrate_interface.return_value = mock_instance
        
        # Create client and connect
        client = SubstrateClient(self.valid_url)
        result = client.connect()
        
        # Assertions
        self.assertTrue(result)
        self.assertTrue(client.connected)
        self.assertIsNotNone(client.connection)
        mock_substrate_interface.assert_called_once_with(url=self.valid_url)
    
    @patch('blockchain_interface.client.SubstrateInterface')
    def test_connect_failure(self, mock_substrate_interface):
        """Test connection failure to the blockchain."""
        # Setup mock to raise an exception
        mock_substrate_interface.side_effect = Exception("Connection failed")
        
        # Create client and attempt to connect
        client = SubstrateClient(self.valid_url)
        
        # Assert that connection raises an error after retries
        with self.assertRaises(ConnectionError) as context:
            client.connect()
        
        self.assertIn("Failed to connect", str(context.exception))
        self.assertFalse(client.connected)
        self.assertIsNone(client.connection)
    
    @patch('blockchain_interface.client.SubstrateInterface')
    def test_disconnect(self, mock_substrate_interface):
        """Test disconnection from the blockchain."""
        # Setup mock
        mock_instance = MagicMock()
        mock_substrate_interface.return_value = mock_instance
        
        # Create client, connect, and then disconnect
        client = SubstrateClient(self.valid_url)
        client.connect()
        client.disconnect()
        
        # Assertions
        self.assertFalse(client.connected)
        self.assertIsNone(client.connection)
        # Verify close was called on the connection
        mock_instance.close.assert_called_once()
    
    @patch('blockchain_interface.client.SubstrateInterface')
    def test_execute_rpc_success(self, mock_substrate_interface):
        """Test successful RPC execution."""
        # Setup mock
        mock_instance = MagicMock()
        mock_response = {"result": "success"}
        mock_instance.rpc_request.return_value = mock_response
        mock_substrate_interface.return_value = mock_instance
        
        # Create client, connect, and execute RPC
        client = SubstrateClient(self.valid_url)
        client.connect()
        method = "test_method"
        params = ["param1", "param2"]
        result = client.execute_rpc(method, params)
        
        # Assertions
        self.assertEqual(result, mock_response)
        mock_instance.rpc_request.assert_called_once_with(method, params)
    
    @patch('blockchain_interface.client.SubstrateInterface')
    def test_execute_rpc_not_connected(self, mock_substrate_interface):
        """Test RPC execution when not connected."""
        # Create client without connecting
        client = SubstrateClient(self.valid_url)
        
        # Attempt to execute RPC
        with self.assertRaises(ConnectionError) as context:
            client.execute_rpc("test_method")
        
        self.assertIn("Not connected", str(context.exception))
    
    @patch('blockchain_interface.client.SubstrateInterface')
    def test_execute_rpc_failure(self, mock_substrate_interface):
        """Test RPC execution failure."""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.rpc_request.side_effect = Exception("RPC failed")
        mock_substrate_interface.return_value = mock_instance
        
        # Create client, connect, and attempt to execute RPC
        client = SubstrateClient(self.valid_url)
        client.connect()
        
        # Assert that RPC execution raises an error
        with self.assertRaises(RuntimeError) as context:
            client.execute_rpc("test_method")
        
        self.assertIn("RPC execution failed", str(context.exception))
    
    @patch('blockchain_interface.client.SubstrateInterface')
    def test_context_manager(self, mock_substrate_interface):
        """Test using the client as a context manager."""
        # Setup mock
        mock_instance = MagicMock()
        mock_substrate_interface.return_value = mock_instance
        
        # Use client as context manager
        with SubstrateClient(self.valid_url) as client:
            self.assertTrue(client.connected)
            self.assertIsNotNone(client.connection)
        
        # After context exit
        self.assertFalse(client.connected)
        self.assertIsNone(client.connection)
        mock_instance.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
