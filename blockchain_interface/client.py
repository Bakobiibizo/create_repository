"""
Substrate Client for ComAI Client.

This module provides a high-level interface for interacting with the CommuneAI blockchain
using the Substrate interface. It handles connection initialization, RPC command execution,
and error handling.
"""

from typing import Dict, List, Optional, Union, Any
import logging
import time
from urllib.parse import urlparse

from substrateinterface import SubstrateInterface
from websocket import WebSocketConnectionClosedException

logger = logging.getLogger(__name__)


class SubstrateClient:
    """
    A client for interacting with the CommuneAI blockchain using Substrate interface.
    
    This class provides methods for connecting to the blockchain, executing RPC commands,
    and handling errors and retries.
    
    Attributes:
        url (str): The WebSocket URL of the blockchain node.
        retry_attempts (int): Number of retry attempts for failed operations.
        retry_delay (float): Delay between retry attempts in seconds.
        connection (Optional[SubstrateInterface]): The active connection to the blockchain.
        connected (bool): Whether the client is currently connected.
    """
    
    def __init__(
        self, 
        url: str, 
        retry_attempts: int = 3, 
        retry_delay: float = 1.0
    ):
        """
        Initialize a new SubstrateClient.
        
        Args:
            url (str): The WebSocket URL of the blockchain node.
            retry_attempts (int, optional): Number of retry attempts for failed operations.
                Defaults to 3.
            retry_delay (float, optional): Delay between retry attempts in seconds.
                Defaults to 1.0.
                
        Raises:
            ValueError: If the URL is invalid or not a WebSocket URL.
        """
        self.url = url
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.connection = None
        self.connected = False
        
        # Validate URL
        parsed_url = urlparse(url)
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
        try:
            return self._retry_operation(self._connect_impl)
        except Exception as e:
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
        Retry an operation with exponential backoff.
        
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
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{self.retry_attempts}): {str(e)}"
                )
                if attempt < self.retry_attempts - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
        
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
