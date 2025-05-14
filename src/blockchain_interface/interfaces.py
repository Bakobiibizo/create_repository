"""
Abstract interfaces for blockchain connections.

This module provides abstract base classes for blockchain connections and related components,
enabling dependency injection and better testability.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BlockchainConnectionInterface(ABC):
    """
    Abstract interface for blockchain connections.
    
    This interface defines the contract for classes that provide connections to a blockchain.
    Implementations should handle the details of connection establishment, maintenance, and
    execution of blockchain operations.
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish a connection to the blockchain.
        
        Returns:
            bool: True if connection was successful, False otherwise.
            
        Raises:
            ConnectionError: If connection fails.
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Disconnect from the blockchain.
        
        Returns:
            None
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the connection is active.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        pass
    
    @abstractmethod
    def execute_rpc(self, method: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
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
        pass


class ConnectionManagerInterface(ABC):
    """
    Abstract interface for connection managers.
    
    This interface defines the contract for classes that manage pools of blockchain connections.
    Implementations should handle connection pooling, lifecycle management, and efficient
    resource utilization.
    """
    
    @abstractmethod
    def start(self) -> None:
        """
        Start the connection manager and related background processes.
        
        Returns:
            None
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """
        Stop the connection manager and release all resources.
        
        Returns:
            None
        """
        pass
    
    @abstractmethod
    def get_connection(self) -> Any:
        """
        Get a connection from the pool or create a new one if needed.
        
        Returns:
            Any: A connection object and its identifier.
            
        Raises:
            ConnectionError: If unable to create a connection.
        """
        pass
    
    @abstractmethod
    def release_connection(self, connection_id: str) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection_id (str): The ID of the connection to release.
            
        Returns:
            None
        """
        pass


class ExtrinsicsHandlerInterface(ABC):
    """
    Abstract interface for extrinsics handlers.
    
    This interface defines the contract for classes that handle blockchain extrinsics.
    Implementations should provide methods for submitting and tracking extrinsics.
    """
    
    @abstractmethod
    def submit_extrinsic(self, module: str, call: str, params: Dict[str, Any], account: Any) -> str:
        """
        Submit an extrinsic to the blockchain.
        
        Args:
            module (str): The module containing the call.
            call (str): The call to execute.
            params (Dict[str, Any]): Parameters for the call.
            account (Any): The account to sign the extrinsic.
            
        Returns:
            str: The hash of the submitted extrinsic.
            
        Raises:
            ValueError: If parameters are invalid.
            RuntimeError: If submission fails.
        """
        pass
    
    @abstractmethod
    def get_extrinsic_status(self, extrinsic_hash: str) -> Dict[str, Any]:
        """
        Get the status of a submitted extrinsic.
        
        Args:
            extrinsic_hash (str): The hash of the extrinsic.
            
        Returns:
            Dict[str, Any]: The status of the extrinsic.
            
        Raises:
            ValueError: If the hash is invalid.
            RuntimeError: If status retrieval fails.
        """
        pass


class StorageQueryInterface(ABC):
    """
    Abstract interface for storage queries.
    
    This interface defines the contract for classes that handle blockchain storage queries.
    Implementations should provide methods for querying and subscribing to storage.
    """
    
    @abstractmethod
    def query_storage(self, module: str, storage_item: str, params: Optional[List[Any]] = None) -> Any:
        """
        Query a storage item from the blockchain.
        
        Args:
            module (str): The module containing the storage item.
            storage_item (str): The storage item to query.
            params (Optional[List[Any]], optional): Parameters for the query.
                Defaults to None.
                
        Returns:
            Any: The value of the storage item.
            
        Raises:
            ValueError: If parameters are invalid.
            RuntimeError: If query fails.
        """
        pass
    
    @abstractmethod
    def subscribe_storage(self, module: str, storage_item: str, callback: callable, params: Optional[List[Any]] = None) -> str:
        """
        Subscribe to changes in a storage item.
        
        Args:
            module (str): The module containing the storage item.
            storage_item (str): The storage item to subscribe to.
            callback (callable): Function to call when the storage item changes.
            params (Optional[List[Any]], optional): Parameters for the subscription.
                Defaults to None.
                
        Returns:
            str: The subscription ID.
            
        Raises:
            ValueError: If parameters are invalid.
            RuntimeError: If subscription fails.
        """
        pass
    
    @abstractmethod
    def unsubscribe_storage(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a storage subscription.
        
        Args:
            subscription_id (str): The ID of the subscription.
            
        Returns:
            bool: True if unsubscription was successful, False otherwise.
            
        Raises:
            ValueError: If the subscription ID is invalid.
            RuntimeError: If unsubscription fails.
        """
        pass


class QueryMapsInterface(ABC):
    """
    Abstract interface for query maps.
    
    This interface defines the contract for classes that handle blockchain query maps.
    Implementations should provide methods for retrieving and caching query maps.
    """
    
    @abstractmethod
    def get_query_map(self, module: str, storage_item: str) -> Dict[str, Any]:
        """
        Get a query map for a storage item.
        
        Args:
            module (str): The module containing the storage item.
            storage_item (str): The storage item to get the query map for.
            
        Returns:
            Dict[str, Any]: The query map.
            
        Raises:
            ValueError: If parameters are invalid.
            RuntimeError: If retrieval fails.
        """
        pass
    
    @abstractmethod
    def refresh_query_maps(self) -> None:
        """
        Refresh all cached query maps.
        
        Returns:
            None
            
        Raises:
            RuntimeError: If refresh fails.
        """
        pass
