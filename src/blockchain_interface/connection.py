"""
Connection Manager for ComAI Client.

This module provides a connection pool manager for WebSocket connections to the CommuneAI blockchain.
It handles connection lifecycle, pooling, and reconnection logic for efficient resource utilization.
"""

import logging
import threading
import time
import queue
import random
from typing import Dict, List, Optional, Tuple, Any, Callable, Type
from urllib.parse import urlparse
import concurrent.futures

from websocket import WebSocketConnectionClosedException
from substrateinterface import SubstrateInterface

from src.utilities.environment_manager import get_environment_manager
from src.utilities.path_manager import get_path_manager
from src.utilities.console_manager import get_console_manager
from src.blockchain_interface.interfaces import ConnectionManagerInterface, BlockchainConnectionInterface

logger = logging.getLogger(__name__)


class ConnectionManager(ConnectionManagerInterface):
    """
    Manages a pool of WebSocket connections to the blockchain.
    
    This class implements the ConnectionManagerInterface and provides methods for creating, 
    reusing, and terminating connections, as well as implementing heartbeat mechanisms and 
    reconnection logic.
    
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
        connection_semaphore (threading.Semaphore): Semaphore for limiting connections.
        connection_timeout (float): Timeout for acquiring a connection.
        connection_priorities (Dict): Dictionary of connection priorities.
        connection_factory (Type): Factory class for creating connections.
    """
    
    def __init__(
        self, 
        url: Optional[str] = None, 
        max_connections: Optional[int] = None, 
        idle_timeout: Optional[float] = None, 
        heartbeat_interval: Optional[float] = None,
        connection_timeout: Optional[float] = None,
        connection_factory: Optional[Type[BlockchainConnectionInterface]] = None,
        config_path: Optional[str] = None
    ):
        """
        Initialize a new ConnectionManager.
        
        Args:
            url (Optional[str], optional): The WebSocket URL of the blockchain node.
                If not provided, it will be read from the environment variable BLOCKCHAIN_URL.
            max_connections (Optional[int], optional): Maximum number of connections to maintain in the pool.
                If not provided, it will be read from the environment variable BLOCKCHAIN_MAX_CONNECTIONS.
                Defaults to 5.
            idle_timeout (Optional[float], optional): Time in seconds after which an idle connection is closed.
                If not provided, it will be read from the environment variable BLOCKCHAIN_IDLE_TIMEOUT.
                Defaults to 300.0.
            heartbeat_interval (Optional[float], optional): Interval in seconds between heartbeat checks.
                If not provided, it will be read from the environment variable BLOCKCHAIN_HEARTBEAT_INTERVAL.
                Defaults to 30.0.
            connection_timeout (Optional[float], optional): Timeout in seconds for acquiring a connection.
                If not provided, it will be read from the environment variable BLOCKCHAIN_CONNECTION_TIMEOUT.
                Defaults to 10.0.
            connection_factory (Optional[Type[BlockchainConnectionInterface]], optional): Factory class for creating connections.
                If not provided, SubstrateInterface will be used directly.
            config_path (Optional[str], optional): Path to the configuration file.
                If not provided, it will use the default path from the path manager.
                
        Raises:
            ValueError: If the URL is invalid or not a WebSocket URL.
        """
        # Get environment manager and path manager
        env_manager = get_environment_manager()
        path_manager = get_path_manager()
        self.console = get_console_manager()
        
        # Get configuration path
        self.config_path = config_path
        if self.config_path is None:
            # Use path manager to get the default configuration path
            self.config_path = path_manager.get_path('blockchain_config', default='~/.comai/blockchain_config.json')
        
        # Get URL from environment if not provided
        self.url = url if url is not None else env_manager.get_var("BLOCKCHAIN_URL", None)
        if self.url is None:
            raise ValueError("No blockchain URL provided and BLOCKCHAIN_URL environment variable not set.")
            
        # Get connection parameters from environment if not provided
        self.max_connections = max_connections if max_connections is not None else env_manager.get_var_as_int("BLOCKCHAIN_MAX_CONNECTIONS", 5)
        self.idle_timeout = idle_timeout if idle_timeout is not None else env_manager.get_var_as_float("BLOCKCHAIN_IDLE_TIMEOUT", 300.0)
        self.heartbeat_interval = heartbeat_interval if heartbeat_interval is not None else env_manager.get_var_as_float("BLOCKCHAIN_HEARTBEAT_INTERVAL", 30.0)
        self.connection_timeout = connection_timeout if connection_timeout is not None else env_manager.get_var_as_float("BLOCKCHAIN_CONNECTION_TIMEOUT", 10.0)
        
        # Initialize connection factory
        self.connection_factory = connection_factory
        
        # Initialize connection pool and semaphore
        self.connection_pool = queue.Queue()
        self.active_connections = {}
        self.connection_semaphore = threading.Semaphore(self.max_connections)
        self.connection_priorities = {}
        
        # Initialize threading components
        self.lock = threading.RLock()
        self.heartbeat_thread = None
        self.running = False
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_connections)
        
        # Validate URL
        parsed_url = urlparse(self.url)
        if not parsed_url.scheme in ['ws', 'wss']:
            raise ValueError(f"Invalid URL scheme: {parsed_url.scheme}. Expected 'ws' or 'wss'.")
            
        self.console.info(f"Initialized connection manager for {self.url} with max {self.max_connections} connections") 
    
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
    
    def get_connection(self, priority: int = 0) -> Tuple[str, Any]:
        """
        Get a connection from the pool or create a new one if needed.
        
        Args:
            priority (int, optional): Priority of the connection request (higher is more important).
                Defaults to 0.
        
        Returns:
            Tuple[str, Any]: A tuple containing the connection ID and the connection.
            
        Raises:
            ConnectionError: If unable to create a connection after retries.
            TimeoutError: If unable to acquire a connection within the timeout period.
        """
        # Try to acquire the semaphore with timeout
        if not self.connection_semaphore.acquire(timeout=self.connection_timeout):
            raise TimeoutError(f"Timed out waiting for a connection after {self.connection_timeout} seconds")
        
        try:
            with self.lock:
                # Store the priority for this request
                request_id = f"req_{id(threading.current_thread())}_{time.time()}"
                self.connection_priorities[request_id] = priority
                
                # Try to get a connection from the pool
                try:
                    if not self.connection_pool.empty():
                        connection_id, connection = self.connection_pool.get_nowait()
                        
                        # Check if the connection is still alive
                        if not self._check_connection(connection):
                            # Connection is dead, create a new one
                            self.console.warning(f"Connection {connection_id} is dead, creating a new one")
                            connection.close()
                            connection_id, connection = self._create_connection()
                    else:
                        # Create a new connection
                        connection_id, connection = self._create_connection()
                    
                    # Add the connection to active connections
                    self.active_connections[connection_id] = {
                        "connection": connection,
                        "last_used": time.time(),
                        "priority": priority
                    }
                    
                    # Remove the priority entry
                    del self.connection_priorities[request_id]
                    
                    return connection_id, connection
                except Exception as e:
                    # Release the semaphore on error
                    self.connection_semaphore.release()
                    # Remove the priority entry
                    if request_id in self.connection_priorities:
                        del self.connection_priorities[request_id]
                    raise ConnectionError(f"Failed to get connection: {str(e)}")
        except Exception as e:
            # Release the semaphore on any error
            self.connection_semaphore.release()
            raise e
    
    def release_connection(self, connection_id: str) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection_id (str): The ID of the connection to release.
            
        Returns:
            None
        """
        try:
            with self.lock:
                if connection_id in self.active_connections:
                    connection = self.active_connections[connection_id]["connection"]
                    del self.active_connections[connection_id]
                    self.connection_pool.put((connection_id, connection))
                    self.console.debug(f"Released connection {connection_id} back to pool")
                else:
                    self.console.warning(f"Attempted to release unknown connection {connection_id}")
        finally:
            # Always release the semaphore
            self.connection_semaphore.release()
    
    def _create_connection(self) -> Tuple[str, Any]:
        """
        Create a new connection to the blockchain.
        
        Returns:
            Tuple[str, Any]: A tuple containing the connection ID and the connection.
            
        Raises:
            ConnectionError: If unable to create a connection.
        """
        try:
            # Use the connection factory if provided, otherwise use SubstrateInterface directly
            if self.connection_factory is not None:
                connection = self.connection_factory(url=self.url)
                # Ensure connection is established
                if hasattr(connection, 'connect'):
                    connection.connect()
            else:
                connection = SubstrateInterface(url=self.url)
                
            connection_id = f"conn_{id(connection)}_{time.time()}"
            self.console.debug(f"Created new connection {connection_id}")
            return connection_id, connection
        except Exception as e:
            self.console.error(f"Failed to create connection: {str(e)}")
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
