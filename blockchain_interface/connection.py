"""
Connection Manager for ComAI Client.

This module provides a connection pool manager for WebSocket connections to the CommuneAI blockchain.
It handles connection lifecycle, pooling, and reconnection logic for efficient resource utilization.
"""

import logging
import threading
import time
import queue
from typing import Dict, List, Optional, Tuple, Any, Callable
from urllib.parse import urlparse

from websocket import WebSocketConnectionClosedException
from substrateinterface import SubstrateInterface

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages a pool of WebSocket connections to the blockchain.
    
    This class provides methods for creating, reusing, and terminating connections,
    as well as implementing heartbeat mechanisms and reconnection logic.
    
    Attributes:
        url (str): The WebSocket URL of the blockchain node.
        max_connections (int): Maximum number of connections to maintain in the pool.
        idle_timeout (float): Time in seconds after which an idle connection is closed.
        heartbeat_interval (float): Interval in seconds between heartbeat checks.
        connection_pool (queue.Queue): Pool of available connections.
        active_connections (Dict): Dictionary of active connections and their metadata.
        lock (threading.RLock): Lock for thread-safe operations.
        heartbeat_thread (threading.Thread): Thread for running heartbeat checks.
        running (bool): Whether the connection manager is running.
    """
    
    def __init__(
        self, 
        url: str, 
        max_connections: int = 5, 
        idle_timeout: float = 300.0, 
        heartbeat_interval: float = 30.0
    ):
        """
        Initialize a new ConnectionManager.
        
        Args:
            url (str): The WebSocket URL of the blockchain node.
            max_connections (int, optional): Maximum number of connections to maintain in the pool.
                Defaults to 5.
            idle_timeout (float, optional): Time in seconds after which an idle connection is closed.
                Defaults to 300.0 (5 minutes).
            heartbeat_interval (float, optional): Interval in seconds between heartbeat checks.
                Defaults to 30.0.
                
        Raises:
            ValueError: If the URL is invalid or not a WebSocket URL.
        """
        self.url = url
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout
        self.heartbeat_interval = heartbeat_interval
        self.connection_pool = queue.Queue()
        self.active_connections = {}
        self.lock = threading.RLock()
        self.heartbeat_thread = None
        self.running = False
        
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme in ['ws', 'wss']:
            raise ValueError(f"Invalid URL scheme: {parsed_url.scheme}. Expected 'ws' or 'wss'.")
    
    def start(self) -> None:
        """
        Start the connection manager and heartbeat thread.
        
        Returns:
            None
        """
        with self.lock:
            if not self.running:
                self.running = True
                self.heartbeat_thread = threading.Thread(
                    target=self._run_heartbeat,
                    daemon=True
                )
                self.heartbeat_thread.start()
    
    def stop(self) -> None:
        """
        Stop the connection manager and close all connections.
        
        Returns:
            None
        """
        with self.lock:
            self.running = False
            
            # Close all connections in the pool
            while not self.connection_pool.empty():
                try:
                    _, connection = self.connection_pool.get_nowait()
                    connection.close()
                except queue.Empty:
                    break
            
            # Close all active connections
            for connection_data in self.active_connections.values():
                connection_data["connection"].close()
            
            self.active_connections = {}
    
    def get_connection(self) -> Tuple[str, SubstrateInterface]:
        """
        Get a connection from the pool or create a new one if needed.
        
        Returns:
            Tuple[str, SubstrateInterface]: A tuple containing the connection ID and the connection.
            
        Raises:
            ConnectionError: If unable to create a connection after retries.
        """
        with self.lock:
            # Check if we've reached the maximum number of connections
            if len(self.active_connections) >= self.max_connections and self.connection_pool.empty():
                raise ConnectionError(f"Maximum number of connections reached ({self.max_connections})")
            
            # Try to get a connection from the pool
            try:
                if not self.connection_pool.empty():
                    connection_id, connection = self.connection_pool.get_nowait()
                    
                    # Check if the connection is still alive
                    if not self._check_connection(connection):
                        # Connection is dead, create a new one
                        connection.close()
                        connection_id, connection = self._create_connection()
                else:
                    # Create a new connection
                    connection_id, connection = self._create_connection()
                
                # Add the connection to active connections
                self.active_connections[connection_id] = {
                    "connection": connection,
                    "last_used": time.time()
                }
                
                return connection_id, connection
            except Exception as e:
                raise ConnectionError(f"Failed to get connection: {str(e)}")
    
    def release_connection(self, connection_id: str) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection_id (str): The ID of the connection to release.
            
        Returns:
            None
        """
        with self.lock:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]["connection"]
                del self.active_connections[connection_id]
                self.connection_pool.put((connection_id, connection))
    
    def _create_connection(self) -> Tuple[str, SubstrateInterface]:
        """
        Create a new connection to the blockchain.
        
        Returns:
            Tuple[str, SubstrateInterface]: A tuple containing the connection ID and the connection.
            
        Raises:
            ConnectionError: If unable to create a connection.
        """
        try:
            connection = SubstrateInterface(url=self.url)
            connection_id = f"conn_{id(connection)}_{time.time()}"
            return connection_id, connection
        except Exception as e:
            raise ConnectionError(f"Failed to create connection: {str(e)}")
    
    def _run_heartbeat(self) -> None:
        """
        Run heartbeat checks on connections and close idle ones.
        
        This method is run in a separate thread and periodically checks the status
        of all connections, closing those that are idle for too long.
        
        Returns:
            None
        """
        while self.running:
            to_remove = []
            current_time = time.time()
            
            with self.lock:
                # Check each active connection
                for connection_id, connection_data in self.active_connections.items():
                    connection = connection_data["connection"]
                    last_used = connection_data["last_used"]
                    
                    # Check if the connection is idle for too long
                    if current_time - last_used > self.idle_timeout:
                        logger.info(f"Closing idle connection {connection_id}")
                        connection.close()
                        to_remove.append(connection_id)
                    # Check if the connection is still alive
                    elif not self._check_connection(connection):
                        logger.warning(f"Connection {connection_id} is dead, closing")
                        connection.close()
                        to_remove.append(connection_id)
                
                # Remove closed connections
                for connection_id in to_remove:
                    if connection_id in self.active_connections:
                        del self.active_connections[connection_id]
            
            # Sleep until next heartbeat check
            time.sleep(self.heartbeat_interval)
    
    def _check_connection(self, connection: SubstrateInterface) -> bool:
        """
        Check if a connection is still alive.
        
        Args:
            connection (SubstrateInterface): The connection to check.
            
        Returns:
            bool: True if the connection is alive, False otherwise.
        """
        try:
            # Try to execute a simple RPC call to check if the connection is alive
            connection.rpc_request("system_health", [])
            return True
        except Exception as e:
            logger.warning(f"Connection check failed: {str(e)}")
            return False
    
    def __enter__(self):
        """
        Enter context manager, starting the connection manager.
        
        Returns:
            ConnectionManager: The connection manager instance.
        """
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager, stopping the connection manager.
        
        Args:
            exc_type: The exception type if an exception was raised.
            exc_val: The exception value if an exception was raised.
            exc_tb: The traceback if an exception was raised.
            
        Returns:
            None
        """
        self.stop()
