"""
Storage Query Manager for ComAI Client.

This module provides functionality for querying blockchain storage and managing subscriptions.
It handles query execution, response parsing, and subscription management.
"""

import logging
import time
import threading
import json
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path

from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException

from src.utilities.environment_manager import get_environment_manager
from src.utilities.path_manager import get_path_manager
from src.utilities.console_manager import get_console_manager
from src.blockchain_interface.interfaces import StorageQueryInterface
from src.blockchain_interface.client import SubstrateClient

logger = logging.getLogger(__name__)


class StorageQueryManager(StorageQueryInterface):
    """
    Manages blockchain storage queries for the ComAI Client.
    
    This class implements the StorageQueryInterface and provides methods for querying
    blockchain storage and managing subscriptions.
    
    Attributes:
        client (SubstrateClient): The blockchain client to use for storage queries.
        cache_path (Path): Path to the storage cache file.
        cache (Dict): Dictionary of cached storage values.
        subscriptions (Dict): Dictionary of active subscriptions.
        cache_ttl (float): Time-to-live for cached values in seconds.
        lock (threading.RLock): Lock for thread-safe operations.
    """
    
    def __init__(
        self,
        client: Optional[SubstrateClient] = None,
        cache_path: Optional[str] = None,
        cache_ttl: Optional[float] = None,
        config_path: Optional[str] = None
    ):
        """
        Initialize a new StorageQueryManager.
        
        Args:
            client (Optional[SubstrateClient], optional): The blockchain client to use.
                If not provided, a new client will be created.
            cache_path (Optional[str], optional): Path to the storage cache file.
                If not provided, it will use the default path from the path manager.
            cache_ttl (Optional[float], optional): Time-to-live for cached values in seconds.
                If not provided, it will be read from the environment variable BLOCKCHAIN_STORAGE_CACHE_TTL.
                Defaults to 60.0.
            config_path (Optional[str], optional): Path to the configuration file.
                If not provided, it will use the default path from the path manager.
                
        Raises:
            ValueError: If the client is invalid.
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
        
        # Get cache TTL from environment if not provided
        self.cache_ttl = cache_ttl if cache_ttl is not None else env_manager.get_var_as_float("BLOCKCHAIN_STORAGE_CACHE_TTL", 60.0)
        
        # Initialize client
        self.client = client
        if self.client is None:
            self.client = SubstrateClient()
            if not self.client.is_connected():
                self.client.connect()
        
        # Get cache path
        if cache_path is None:
            cache_path = path_manager.get_path('storage_cache', default='~/.comai/storage_cache.json')
        self.cache_path = Path(cache_path)
        
        # Ensure cache directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize cache and subscriptions
        self.cache = {}
        self.subscriptions = {}
        self.load_cache()
        
        # Initialize threading components
        self.lock = threading.RLock()
        
        self.console.info(f"Initialized storage query manager with cache at {self.cache_path}")
    
    def query_storage(
        self, 
        module: str, 
        storage_item: str, 
        params: Optional[List[Any]] = None,
        block_hash: Optional[str] = None,
        use_cache: bool = True
    ) -> Any:
        """
        Query a storage item from the blockchain.
        
        Args:
            module (str): The module containing the storage item.
            storage_item (str): The storage item to query.
            params (Optional[List[Any]], optional): Parameters for the query.
                Defaults to None.
            block_hash (Optional[str], optional): Block hash to query at.
                Defaults to None (latest block).
            use_cache (bool, optional): Whether to use the cache.
                Defaults to True.
                
        Returns:
            Any: The value of the storage item.
            
        Raises:
            ValueError: If parameters are invalid.
            RuntimeError: If query fails.
        """
        try:
            # Validate parameters
            if not module:
                raise ValueError("Module name cannot be empty")
            if not storage_item:
                raise ValueError("Storage item name cannot be empty")
            
            # Normalize parameters
            params = params or []
            
            # Create cache key
            cache_key = self._create_cache_key(module, storage_item, params, block_hash)
            
            # Check cache if enabled
            if use_cache:
                cached_value = self._get_from_cache(cache_key)
                if cached_value is not None:
                    self.console.debug(f"Using cached value for {module}.{storage_item}")
                    return cached_value
            
            # Ensure client is connected
            if not self.client.is_connected():
                self.client.connect()
            
            # Get the substrate interface from the client
            substrate = self._get_substrate_interface()
            
            # Query the storage
            self.console.debug(f"Querying storage: {module}.{storage_item} with params: {params}")
            result = substrate.query(
                module=module,
                storage_function=storage_item,
                params=params,
                block_hash=block_hash
            )
            
            # Parse the result
            value = result.value
            
            # Cache the result if caching is enabled
            if use_cache:
                self._add_to_cache(cache_key, value)
            
            return value
            
        except SubstrateRequestException as e:
            self.console.error(f"Substrate request error: {str(e)}")
            raise RuntimeError(f"Failed to query storage: {str(e)}")
        except Exception as e:
            self.console.error(f"Error querying storage: {str(e)}")
            raise RuntimeError(f"Failed to query storage: {str(e)}")
    
    def subscribe_storage(
        self, 
        module: str, 
        storage_item: str, 
        callback: Callable[[Any], None], 
        params: Optional[List[Any]] = None
    ) -> str:
        """
        Subscribe to changes in a storage item.
        
        Args:
            module (str): The module containing the storage item.
            storage_item (str): The storage item to subscribe to.
            callback (Callable[[Any], None]): Function to call when the storage item changes.
            params (Optional[List[Any]], optional): Parameters for the subscription.
                Defaults to None.
                
        Returns:
            str: The subscription ID.
            
        Raises:
            ValueError: If parameters are invalid.
            RuntimeError: If subscription fails.
        """
        try:
            # Validate parameters
            if not module:
                raise ValueError("Module name cannot be empty")
            if not storage_item:
                raise ValueError("Storage item name cannot be empty")
            if not callable(callback):
                raise ValueError("Callback must be callable")
            
            # Normalize parameters
            params = params or []
            
            # Ensure client is connected
            if not self.client.is_connected():
                self.client.connect()
            
            # Get the substrate interface from the client
            substrate = self._get_substrate_interface()
            
            # Create subscription key
            subscription_key = f"{module}.{storage_item}.{hash(tuple(params))}"
            
            # Check if we already have a subscription for this key
            with self.lock:
                if subscription_key in self.subscriptions:
                    # Add the callback to the existing subscription
                    subscription_id = f"{subscription_key}.{len(self.subscriptions[subscription_key]['callbacks'])}"
                    self.subscriptions[subscription_key]["callbacks"][subscription_id] = callback
                    self.console.debug(f"Added callback to existing subscription for {module}.{storage_item}")
                    return subscription_id
            
            # Create a new subscription
            self.console.debug(f"Creating new subscription for {module}.{storage_item}")
            
            # Define the callback wrapper
            def subscription_callback(obj, update_nr, subscription_id):
                try:
                    # Get the value from the update
                    value = obj.value
                    
                    # Call all callbacks for this subscription
                    with self.lock:
                        if subscription_key in self.subscriptions:
                            for callback_id, cb in self.subscriptions[subscription_key]["callbacks"].items():
                                try:
                                    cb(value)
                                except Exception as e:
                                    self.console.error(f"Error in subscription callback {callback_id}: {str(e)}")
                except Exception as e:
                    self.console.error(f"Error processing subscription update: {str(e)}")
            
            # Create the subscription
            substrate_subscription = substrate.query_map(
                module=module,
                storage_function=storage_item,
                params=params,
                subscription_handler=subscription_callback
            )
            
            # Store the subscription
            with self.lock:
                subscription_id = f"{subscription_key}.0"
                self.subscriptions[subscription_key] = {
                    "substrate_subscription": substrate_subscription,
                    "callbacks": {subscription_id: callback},
                    "module": module,
                    "storage_item": storage_item,
                    "params": params
                }
            
            return subscription_id
            
        except SubstrateRequestException as e:
            self.console.error(f"Substrate request error: {str(e)}")
            raise RuntimeError(f"Failed to create subscription: {str(e)}")
        except Exception as e:
            self.console.error(f"Error creating subscription: {str(e)}")
            raise RuntimeError(f"Failed to create subscription: {str(e)}")
    
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
        try:
            # Validate parameters
            if not subscription_id:
                raise ValueError("Subscription ID cannot be empty")
            
            # Parse the subscription ID
            parts = subscription_id.split(".")
            if len(parts) < 2:
                raise ValueError(f"Invalid subscription ID format: {subscription_id}")
            
            # Get the subscription key and callback ID
            subscription_key = ".".join(parts[:-1])
            callback_id = subscription_id
            
            # Check if we have this subscription
            with self.lock:
                if subscription_key not in self.subscriptions:
                    self.console.warning(f"Subscription {subscription_key} not found")
                    return False
                
                # Remove the callback
                if callback_id in self.subscriptions[subscription_key]["callbacks"]:
                    del self.subscriptions[subscription_key]["callbacks"][callback_id]
                    self.console.debug(f"Removed callback {callback_id} from subscription {subscription_key}")
                
                # If there are no more callbacks, unsubscribe from the substrate
                if not self.subscriptions[subscription_key]["callbacks"]:
                    # Unsubscribe from the substrate
                    substrate_subscription = self.subscriptions[subscription_key]["substrate_subscription"]
                    substrate_subscription.unsubscribe()
                    
                    # Remove the subscription
                    del self.subscriptions[subscription_key]
                    self.console.debug(f"Removed subscription {subscription_key}")
            
            return True
            
        except Exception as e:
            self.console.error(f"Error unsubscribing: {str(e)}")
            raise RuntimeError(f"Failed to unsubscribe: {str(e)}")
    
    def load_cache(self) -> None:
        """
        Load the storage cache from disk.
        
        Returns:
            None
        """
        try:
            if self.cache_path.exists():
                with open(self.cache_path, 'r') as f:
                    data = json.load(f)
                    
                    # Validate and filter data
                    if isinstance(data, dict):
                        # Filter out expired entries
                        current_time = time.time()
                        filtered_data = {
                            k: v for k, v in data.items()
                            if current_time - v.get("timestamp", 0) < self.cache_ttl
                        }
                        
                        self.cache = filtered_data
                        self.console.debug(f"Loaded {len(self.cache)} cached storage values")
        except Exception as e:
            self.console.error(f"Failed to load storage cache: {str(e)}")
            # Initialize empty dict if loading fails
            self.cache = {}
    
    def save_cache(self) -> None:
        """
        Save the storage cache to disk.
        
        Returns:
            None
        """
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
            self.console.debug(f"Saved {len(self.cache)} cached storage values")
        except Exception as e:
            self.console.error(f"Failed to save storage cache: {str(e)}")
    
    def clear_cache(self) -> None:
        """
        Clear the storage cache.
        
        Returns:
            None
        """
        with self.lock:
            self.cache = {}
            self.save_cache()
            self.console.info("Cleared storage cache")
    
    def _create_cache_key(
        self, 
        module: str, 
        storage_item: str, 
        params: List[Any], 
        block_hash: Optional[str]
    ) -> str:
        """
        Create a cache key for a storage query.
        
        Args:
            module (str): The module containing the storage item.
            storage_item (str): The storage item to query.
            params (List[Any]): Parameters for the query.
            block_hash (Optional[str]): Block hash to query at.
            
        Returns:
            str: The cache key.
        """
        # Convert params to a string representation
        params_str = json.dumps(params, sort_keys=True, default=str)
        
        # Create the key
        key = f"{module}.{storage_item}.{params_str}"
        
        # Add block hash if provided
        if block_hash:
            key += f".{block_hash}"
            
        return key
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key (str): The cache key.
            
        Returns:
            Optional[Any]: The cached value, or None if not found or expired.
        """
        with self.lock:
            if key in self.cache:
                # Check if the entry is expired
                entry = self.cache[key]
                if time.time() - entry["timestamp"] < self.cache_ttl:
                    return entry["value"]
                else:
                    # Remove expired entry
                    del self.cache[key]
                    
            return None
    
    def _add_to_cache(self, key: str, value: Any) -> None:
        """
        Add a value to the cache.
        
        Args:
            key (str): The cache key.
            value (Any): The value to cache.
            
        Returns:
            None
        """
        with self.lock:
            self.cache[key] = {
                "value": value,
                "timestamp": time.time()
            }
            
            # Periodically save the cache
            if len(self.cache) % 10 == 0:
                self.save_cache()
    
    def _get_substrate_interface(self) -> SubstrateInterface:
        """
        Get the substrate interface from the client.
        
        Returns:
            SubstrateInterface: The substrate interface.
            
        Raises:
            RuntimeError: If the client is not connected.
        """
        if not hasattr(self.client, "connection") or self.client.connection is None:
            raise RuntimeError("Client is not connected")
        
        return self.client.connection
