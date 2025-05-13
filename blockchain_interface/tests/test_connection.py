"""
Tests for the ConnectionManager class.
"""

import unittest
import threading
import time
import queue
from unittest.mock import patch, MagicMock, call
import pytest
from urllib.parse import urlparse

from blockchain_interface.connection import ConnectionManager
from substrateinterface import SubstrateInterface


class TestConnectionManager(unittest.TestCase):
    """Test cases for the ConnectionManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_url = "ws://localhost:9944"
        self.invalid_url = "http://localhost:9944"
        self.max_connections = 3
        self.idle_timeout = 10.0
        self.heartbeat_interval = 1.0
    
    def test_init_with_valid_url(self):
        """Test initialization with a valid WebSocket URL."""
        manager = ConnectionManager(self.valid_url)
        self.assertEqual(manager.url, self.valid_url)
        self.assertEqual(manager.max_connections, 5)  # Default value
        self.assertEqual(manager.idle_timeout, 300.0)  # Default value
        self.assertEqual(manager.heartbeat_interval, 30.0)  # Default value
        self.assertIsInstance(manager.connection_pool, queue.Queue)
        self.assertEqual(manager.connection_pool.qsize(), 0)
        self.assertEqual(manager.active_connections, {})
        self.assertIsNone(manager.heartbeat_thread)
        self.assertFalse(manager.running)
    
    def test_init_with_invalid_url(self):
        """Test initialization with an invalid URL scheme."""
        with self.assertRaises(ValueError) as context:
            ConnectionManager(self.invalid_url)
        self.assertIn("Invalid URL scheme", str(context.exception))
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        manager = ConnectionManager(
            self.valid_url,
            max_connections=self.max_connections,
            idle_timeout=self.idle_timeout,
            heartbeat_interval=self.heartbeat_interval
        )
        self.assertEqual(manager.max_connections, self.max_connections)
        self.assertEqual(manager.idle_timeout, self.idle_timeout)
        self.assertEqual(manager.heartbeat_interval, self.heartbeat_interval)
    
    @patch('blockchain_interface.connection.threading.Thread')
    def test_start(self, mock_thread):
        """Test starting the connection manager."""
        # Setup mock
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Create manager and start it
        manager = ConnectionManager(self.valid_url)
        manager.start()
        
        # Assertions
        self.assertTrue(manager.running)
        mock_thread.assert_called_once_with(
            target=manager._run_heartbeat,
            daemon=True
        )
        mock_thread_instance.start.assert_called_once()
        self.assertEqual(manager.heartbeat_thread, mock_thread_instance)
    
    @patch('blockchain_interface.connection.threading.Thread')
    def test_start_already_running(self, mock_thread):
        """Test starting the connection manager when it's already running."""
        # Setup mock
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Create manager and start it twice
        manager = ConnectionManager(self.valid_url)
        manager.running = True
        manager.heartbeat_thread = mock_thread_instance
        manager.start()
        
        # Assertions
        self.assertTrue(manager.running)
        mock_thread.assert_not_called()
    
    def test_stop(self):
        """Test stopping the connection manager."""
        # Create manager with mock connections
        manager = ConnectionManager(self.valid_url)
        manager.running = True
        
        # Add some mock connections to the pool and active connections
        mock_connection1 = MagicMock()
        mock_connection2 = MagicMock()
        manager.connection_pool.put(("conn1", mock_connection1))
        manager.active_connections = {
            "conn2": {
                "connection": mock_connection2,
                "last_used": time.time()
            }
        }
        
        # Stop the manager
        manager.stop()
        
        # Assertions
        self.assertFalse(manager.running)
        self.assertTrue(manager.connection_pool.empty())
        self.assertEqual(manager.active_connections, {})
        mock_connection1.close.assert_called_once()
        mock_connection2.close.assert_called_once()
    
    @patch('blockchain_interface.connection.SubstrateInterface')
    def test_get_connection_from_pool(self, mock_substrate_interface):
        """Test getting a connection from the pool."""
        # Setup mock
        mock_connection = MagicMock()
        
        # Create manager
        manager = ConnectionManager(self.valid_url)
        manager.running = True
        
        # Add a connection to the pool
        connection_id = "test_conn_id"
        manager.connection_pool.put((connection_id, mock_connection))
        
        # Get the connection
        result_id, result_conn = manager.get_connection()
        
        # Assertions
        self.assertEqual(result_id, connection_id)
        self.assertEqual(result_conn, mock_connection)
        self.assertEqual(len(manager.active_connections), 1)
        self.assertIn(connection_id, manager.active_connections)
        self.assertEqual(manager.active_connections[connection_id]["connection"], mock_connection)
        self.assertIsNotNone(manager.active_connections[connection_id]["last_used"])
        mock_substrate_interface.assert_not_called()  # Should not create a new connection
    
    @patch('blockchain_interface.connection.SubstrateInterface')
    def test_get_connection_create_new(self, mock_substrate_interface):
        """Test getting a connection when pool is empty."""
        # Setup mock
        mock_connection = MagicMock()
        mock_substrate_interface.return_value = mock_connection
        
        # Create manager
        manager = ConnectionManager(self.valid_url)
        manager.running = True
        
        # Get a connection (should create a new one)
        result_id, result_conn = manager.get_connection()
        
        # Assertions
        self.assertIsNotNone(result_id)
        self.assertEqual(result_conn, mock_connection)
        self.assertEqual(len(manager.active_connections), 1)
        self.assertIn(result_id, manager.active_connections)
        self.assertEqual(manager.active_connections[result_id]["connection"], mock_connection)
        self.assertIsNotNone(manager.active_connections[result_id]["last_used"])
        mock_substrate_interface.assert_called_once_with(url=self.valid_url)
    
    @patch('blockchain_interface.connection.SubstrateInterface')
    def test_get_connection_max_reached(self, mock_substrate_interface):
        """Test getting a connection when max connections is reached."""
        # Setup mock
        mock_connection = MagicMock()
        mock_substrate_interface.return_value = mock_connection
        
        # Create manager with max_connections=1
        manager = ConnectionManager(self.valid_url, max_connections=1)
        manager.running = True
        
        # Add a connection to active_connections
        existing_id = "existing_conn"
        existing_conn = MagicMock()
        manager.active_connections = {
            existing_id: {
                "connection": existing_conn,
                "last_used": time.time()
            }
        }
        
        # Try to get a connection (should wait for one to be released)
        with self.assertRaises(ConnectionError) as context:
            manager.get_connection()
        
        self.assertIn("Maximum number of connections reached", str(context.exception))
        mock_substrate_interface.assert_not_called()
    
    def test_release_connection_to_pool(self):
        """Test releasing a connection back to the pool."""
        # Create manager
        manager = ConnectionManager(self.valid_url)
        manager.running = True
        
        # Add a connection to active_connections
        connection_id = "test_conn_id"
        mock_connection = MagicMock()
        manager.active_connections = {
            connection_id: {
                "connection": mock_connection,
                "last_used": time.time()
            }
        }
        
        # Release the connection
        manager.release_connection(connection_id)
        
        # Assertions
        self.assertEqual(len(manager.active_connections), 0)
        self.assertEqual(manager.connection_pool.qsize(), 1)
        pool_id, pool_conn = manager.connection_pool.get()
        self.assertEqual(pool_id, connection_id)
        self.assertEqual(pool_conn, mock_connection)
    
    def test_release_connection_unknown_id(self):
        """Test releasing a connection with unknown ID."""
        # Create manager
        manager = ConnectionManager(self.valid_url)
        manager.running = True
        
        # Release a non-existent connection
        manager.release_connection("unknown_id")
        
        # Assertions
        self.assertEqual(len(manager.active_connections), 0)
        self.assertEqual(manager.connection_pool.qsize(), 0)
    
    @patch('blockchain_interface.connection.SubstrateInterface')
    def test_create_connection_success(self, mock_substrate_interface):
        """Test creating a new connection successfully."""
        # Setup mock
        mock_connection = MagicMock()
        mock_substrate_interface.return_value = mock_connection
        
        # Create manager
        manager = ConnectionManager(self.valid_url)
        
        # Create a connection
        connection_id, connection = manager._create_connection()
        
        # Assertions
        self.assertIsNotNone(connection_id)
        self.assertEqual(connection, mock_connection)
        mock_substrate_interface.assert_called_once_with(url=self.valid_url)
    
    @patch('blockchain_interface.connection.SubstrateInterface')
    def test_create_connection_failure(self, mock_substrate_interface):
        """Test creating a new connection with failure."""
        # Setup mock to raise an exception
        mock_substrate_interface.side_effect = Exception("Connection failed")
        
        # Create manager
        manager = ConnectionManager(self.valid_url)
        
        # Attempt to create a connection
        with self.assertRaises(ConnectionError) as context:
            manager._create_connection()
        
        self.assertIn("Failed to create connection", str(context.exception))
        mock_substrate_interface.assert_called_once_with(url=self.valid_url)
    
    def test_check_connection_alive(self):
        """Test checking a connection that is alive."""
        # Create manager
        manager = ConnectionManager(self.valid_url)
        
        # Create a mock connection that responds to a ping
        mock_connection = MagicMock()
        mock_connection.rpc_request.return_value = {"result": "pong"}
        
        # Check the connection
        result = manager._check_connection(mock_connection)
        
        # Assertions
        self.assertTrue(result)
        mock_connection.rpc_request.assert_called_once_with("system_health", [])
    
    def test_check_connection_dead(self):
        """Test checking a connection that is dead."""
        # Create manager
        manager = ConnectionManager(self.valid_url)
        
        # Create a mock connection that raises an exception on ping
        mock_connection = MagicMock()
        mock_connection.rpc_request.side_effect = Exception("Connection lost")
        
        # Check the connection
        result = manager._check_connection(mock_connection)
        
        # Assertions
        self.assertFalse(result)
        mock_connection.rpc_request.assert_called_once_with("system_health", [])
    
    @patch('blockchain_interface.connection.time.sleep')
    def test_run_heartbeat(self, mock_sleep):
        """Test the heartbeat thread function."""
        # Setup mocks
        mock_sleep.side_effect = [None, Exception("Stop loop")]  # Run loop twice
        
        # Create manager with mock connections
        manager = ConnectionManager(
            self.valid_url,
            idle_timeout=1.0,
            heartbeat_interval=1.0
        )
        manager.running = True
        
        # Add some connections with different last_used times
        current_time = time.time()
        mock_conn1 = MagicMock()  # Recent connection
        mock_conn2 = MagicMock()  # Idle connection
        mock_conn3 = MagicMock()  # Dead connection
        
        manager.active_connections = {
            "conn1": {
                "connection": mock_conn1,
                "last_used": current_time
            },
            "conn2": {
                "connection": mock_conn2,
                "last_used": current_time - 2.0  # Idle (> idle_timeout)
            },
            "conn3": {
                "connection": mock_conn3,
                "last_used": current_time - 0.5
            }
        }
        
        # Mock the _check_connection method
        manager._check_connection = MagicMock()
        manager._check_connection.side_effect = lambda conn: conn != mock_conn3
        
        # Run the heartbeat function (will run twice due to mock_sleep)
        with self.assertRaises(Exception) as context:
            manager._run_heartbeat()
        
        self.assertIn("Stop loop", str(context.exception))
        
        # Assertions
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_called_with(1.0)
        
        # Check that idle and dead connections were closed
        mock_conn1.close.assert_not_called()  # Recent connection should not be closed
        mock_conn2.close.assert_called_once()  # Idle connection should be closed
        mock_conn3.close.assert_called_once()  # Dead connection should be closed
        
        # Check that active_connections was updated
        self.assertEqual(len(manager.active_connections), 1)
        self.assertIn("conn1", manager.active_connections)
        self.assertNotIn("conn2", manager.active_connections)
        self.assertNotIn("conn3", manager.active_connections)
    
    @patch('blockchain_interface.connection.threading.Thread')
    def test_context_manager(self, mock_thread):
        """Test using the connection manager as a context manager."""
        # Setup mock
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Use manager as context manager
        with ConnectionManager(self.valid_url) as manager:
            self.assertTrue(manager.running)
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
        
        # After context exit
        self.assertFalse(manager.running)


if __name__ == "__main__":
    unittest.main()
