"""
Substrate Client for ComAI Client.

This module provides a high-level interface for interacting with the CommuneAI blockchain
using the Substrate interface. It handles connection initialization, RPC command execution,
and error handling.
"""

from typing import Dict, List, Optional, Union, Any, Tuple
import logging
import time
import random
from urllib.parse import urlparse

from substrateinterface import SubstrateInterface
from websocket import WebSocketConnectionClosedException

from src.utilities.environment_manager import get_environment_manager
from src.utilities.path_manager import get_path_manager
from src.blockchain_interface.interfaces import BlockchainConnectionInterface

logger = logging.getLogger(__name__)


class SubstrateClient(BlockchainConnectionInterface):
    """
    A client for interacting with the CommuneAI blockchain using Substrate interface.
    
    This class implements the BlockchainConnectionInterface and provides methods for 
    connecting to the blockchain, executing RPC commands, and handling errors and retries.
    
    Attributes:
        url (str): The WebSocket URL of the blockchain node.
        retry_attempts (int): Number of retry attempts for failed operations.
        retry_delay (float): Delay between retry attempts in seconds.
        connection (Optional[SubstrateInterface]): The active connection to the blockchain.
        connected (bool): Whether the client is currently connected.
        circuit_breaker_threshold (int): Number of consecutive failures before circuit breaker trips.
        circuit_breaker_reset_time (float): Time in seconds before circuit breaker resets.
        circuit_breaker_failures (int): Current count of consecutive failures.
        circuit_breaker_last_failure (float): Timestamp of last failure.
        circuit_breaker_open (bool): Whether the circuit breaker is open (preventing operations).
    """
    
    def __init__(
        self, 
        url: Optional[str] = None, 
        retry_attempts: Optional[int] = None, 
        retry_delay: Optional[float] = None,
        circuit_breaker_threshold: Optional[int] = None,
        circuit_breaker_reset_time: Optional[float] = None,
        config_path: Optional[str] = None
    ):
        """
        Initialize a new SubstrateClient.
        
        Args:
            url (Optional[str], optional): The WebSocket URL of the blockchain node.
                If not provided, it will be read from the environment variable BLOCKCHAIN_URL.
            retry_attempts (Optional[int], optional): Number of retry attempts for failed operations.
                If not provided, it will be read from the environment variable BLOCKCHAIN_RETRY_ATTEMPTS.
                Defaults to 3.
            retry_delay (Optional[float], optional): Delay between retry attempts in seconds.
                If not provided, it will be read from the environment variable BLOCKCHAIN_RETRY_DELAY.
                Defaults to 1.0.
            circuit_breaker_threshold (Optional[int], optional): Number of consecutive failures before circuit breaker trips.
                If not provided, it will be read from the environment variable BLOCKCHAIN_CIRCUIT_BREAKER_THRESHOLD.
                Defaults to 5.
            circuit_breaker_reset_time (Optional[float], optional): Time in seconds before circuit breaker resets.
                If not provided, it will be read from the environment variable BLOCKCHAIN_CIRCUIT_BREAKER_RESET_TIME.
                Defaults to 60.0.
            config_path (Optional[str], optional): Path to the configuration file.
                If not provided, it will use the default path from the path manager.
                
        Raises:
            ValueError: If the URL is invalid or not a WebSocket URL.
        """
        # Get environment manager and path manager
        env_manager = get_environment_manager()
        path_manager = get_path_manager()
        
        # Get configuration path
        self.config_path = config_path
        if self.config_path is None:
            # Use path manager to get the default configuration path
            self.config_path = path_manager.get_path('blockchain_config', default='~/.comai/blockchain_config.json')
        
        # Get URL from environment if not provided
        self.url = url if url is not None else env_manager.get_var("BLOCKCHAIN_URL", None)
        if self.url is None:
            raise ValueError("No blockchain URL provided and BLOCKCHAIN_URL environment variable not set.")
            
        # Get retry parameters from environment if not provided
        self.retry_attempts = retry_attempts if retry_attempts is not None else env_manager.get_var_as_int("BLOCKCHAIN_RETRY_ATTEMPTS", 3)
        self.retry_delay = retry_delay if retry_delay is not None else env_manager.get_var_as_float("BLOCKCHAIN_RETRY_DELAY", 1.0)
        
        # Get circuit breaker parameters from environment if not provided
        self.circuit_breaker_threshold = circuit_breaker_threshold if circuit_breaker_threshold is not None else env_manager.get_var_as_int("BLOCKCHAIN_CIRCUIT_BREAKER_THRESHOLD", 5)
        self.circuit_breaker_reset_time = circuit_breaker_reset_time if circuit_breaker_reset_time is not None else env_manager.get_var_as_float("BLOCKCHAIN_CIRCUIT_BREAKER_RESET_TIME", 60.0)
        
        # Initialize circuit breaker state
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = 0
        self.circuit_breaker_open = False
        
        self.connection = None
        self.connected = False
        
        # Validate URL
        parsed_url = urlparse(self.url)
        if not parsed_url.scheme in ['ws', 'wss']:
            raise ValueError(f"Invalid URL scheme: {parsed_url.scheme}. Expected 'ws' or 'wss'.")
    
    def connect(self) -> bool:
        """
        Establish a connection to the blockchain.
        
        Returns:
            bool: True if connection was successful, False otherwise.
            
        Raises:
            ConnectionError: If connection fails after all retry attempts.
        """
        # Check if circuit breaker is open
        if self._is_circuit_breaker_open():
            logger.warning(f"Circuit breaker is open. Waiting until {self.circuit_breaker_reset_time} seconds have passed since last failure.")
            return False
            
        try:
            return self._retry_operation(self._connect_impl)
        except Exception as e:
            self._record_failure()
            raise ConnectionError(f"Failed to connect to blockchain at {self.url}: {str(e)}")
    
    def disconnect(self) -> None:
        """
        Disconnect from the blockchain.
        
        Returns:
            None
        """
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            self.connected = False
    
    def execute_rpc(
        self, 
        method: str, 
        params: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an RPC command on the blockchain.
        
        Args:
            method (str): The RPC method to execute.
            params (Optional[List[Any]], optional): Parameters for the RPC method.
                Defaults to None.
                
        Returns:
            Dict[str, Any]: The response from the blockchain.
            
        Raises:
            ConnectionError: If not connected to the blockchain.
            ValueError: If the RPC method is invalid.
            RuntimeError: If the RPC execution fails.
        """
        if not self.connected or self.connection is None:
            raise ConnectionError("Not connected to blockchain. Call connect() first.")
            
        if not method:
            raise ValueError("RPC method cannot be empty.")
            
        try:
            return self._retry_operation(self._execute_rpc_impl, method, params or [])
        except Exception as e:
            raise RuntimeError(f"RPC execution failed for method {method}: {str(e)}")
    
    def _retry_operation(self, operation, *args, **kwargs):
        """
        Retry an operation with exponential backoff and jitter.
        
        Args:
            operation: The function to retry.
            *args: Arguments to pass to the operation.
            **kwargs: Keyword arguments to pass to the operation.
            
        Returns:
            The result of the operation if successful.
            
        Raises:
            Exception: The last exception raised by the operation after all retry attempts.
        """
        last_exception = None
        for attempt in range(self.retry_attempts):
            try:
                result = operation(*args, **kwargs)
                # Reset circuit breaker on success
                self._reset_circuit_breaker()
                return result
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{self.retry_attempts}): {str(e)}"
                )
                if attempt < self.retry_attempts - 1:
                    # Exponential backoff with jitter
                    delay = self.retry_delay * (2 ** attempt)
                    # Add jitter (±20% of delay)
                    jitter = delay * 0.2 * (2 * random.random() - 1)
                    delay = max(0, delay + jitter)
                    time.sleep(delay)
        
        # Record failure for circuit breaker
        self._record_failure()
        
        if last_exception:
            raise last_exception
        return None
    
    def _connect_impl(self):
        """
        Internal implementation of connection logic.
        
        Returns:
            bool: True if connection was successful.
            
        Raises:
            Exception: If connection fails.
        """
        self.connection = SubstrateInterface(url=self.url)
        self.connected = True
        return True
        
    def _execute_rpc_impl(self, method, params):
        """
        Internal implementation of RPC execution.
        
        Args:
            method (str): The RPC method to execute.
            params (List[Any]): Parameters for the RPC method.
            
        Returns:
            Dict[str, Any]: The response from the blockchain.
            
        Raises:
            Exception: If RPC execution fails.
        """
        return self.connection.rpc_request(method, params)
    
    def is_connected(self) -> bool:
        """
        Check if the connection is active.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        return self.connected and self.connection is not None
        
    def _is_circuit_breaker_open(self) -> bool:
        """
        Check if the circuit breaker is open.
        
        Returns:
            bool: True if open, False otherwise.
        """
        # If circuit breaker is not open, return False
        if not self.circuit_breaker_open:
            return False
            
        # Check if enough time has passed to reset the circuit breaker
        if time.time() - self.circuit_breaker_last_failure > self.circuit_breaker_reset_time:
            logger.info("Circuit breaker reset time has passed. Resetting circuit breaker.")
            self._reset_circuit_breaker()
            return False
            
        return True
        
    def _record_failure(self) -> None:
        """
        Record a failure for the circuit breaker.
        
        Returns:
            None
        """
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = time.time()
        
        # Check if circuit breaker should trip
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            logger.warning(f"Circuit breaker tripped after {self.circuit_breaker_failures} consecutive failures.")
            self.circuit_breaker_open = True
            
    def _reset_circuit_breaker(self) -> None:
        """
        Reset the circuit breaker.
        
        Returns:
            None
        """
        if self.circuit_breaker_open or self.circuit_breaker_failures > 0:
            logger.info("Resetting circuit breaker.")
        
        self.circuit_breaker_failures = 0
        self.circuit_breaker_open = False
    
    def __enter__(self):
        """
        Enter context manager, establishing a connection.
        
        Returns:
            SubstrateClient: The client instance.
            
        Raises:
            ConnectionError: If connection fails.
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager, closing the connection.
        
        Args:
            exc_type: The exception type if an exception was raised.
            exc_val: The exception value if an exception was raised.
            exc_tb: The traceback if an exception was raised.
            
        Returns:
            None
        """
        self.disconnect()
