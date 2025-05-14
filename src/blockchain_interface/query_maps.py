"""
Query Maps Manager for ComAI Client.

This module provides functionality for retrieving and caching blockchain query maps.
It handles map retrieval, caching, and background refresh.
"""

import logging
import time
import threading
import json
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
import os

from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException

from src.utilities.environment_manager import get_environment_manager
from src.utilities.path_manager import get_path_manager
from src.utilities.console_manager import get_console_manager
from src.blockchain_interface.interfaces import QueryMapsInterface
from src.blockchain_interface.client import SubstrateClient

logger = logging.getLogger(__name__)


class QueryMapsManager(QueryMapsInterface):
    """
    Manages blockchain query maps for the ComAI Client.
    
    This class implements the QueryMapsInterface and provides methods for retrieving
    and caching blockchain query maps.
    
    Attributes:
        client (SubstrateClient): The blockchain client to use for query maps.
        cache_dir (Path): Directory for caching query maps.
        maps_cache (Dict): Dictionary of cached query maps.
        refresh_interval (float): Interval in seconds between background refreshes.
        lock (threading.RLock): Lock for thread-safe operations.
        refresh_thread (threading.Thread): Thread for background refresh.
        running (bool): Whether the refresh thread is running.
    """
    
    def __init__(
        self,
        client: Optional[SubstrateClient] = None,
        cache_dir: Optional[str] = None,
        refresh_interval: Optional[float] = None,
        config_path: Optional[str] = None
    ):
        """
        Initialize a new QueryMapsManager.
        
        Args:
            client (Optional[SubstrateClient], optional): The blockchain client to use.
                If not provided, a new client will be created.
            cache_dir (Optional[str], optional): Directory for caching query maps.
                If not provided, it will use the default path from the path manager.
            refresh_interval (Optional[float], optional): Interval in seconds between background refreshes.
                If not provided, it will be read from the environment variable BLOCKCHAIN_QUERY_MAPS_REFRESH_INTERVAL.
                Defaults to 3600.0 (1 hour).
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
        
        # Get refresh interval from environment if not provided
        self.refresh_interval = refresh_interval if refresh_interval is not None else env_manager.get_var_as_float("BLOCKCHAIN_QUERY_MAPS_REFRESH_INTERVAL", 3600.0)
        
        # Initialize client
        self.client = client
        if self.client is None:
            self.client = SubstrateClient()
            if not self.client.is_connected():
                self.client.connect()
        
        # Get cache directory
        if cache_dir is None:
            cache_dir = path_manager.get_path('query_maps_cache', default='~/.comai/query_maps_cache')
        self.cache_dir = Path(cache_dir)
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize maps cache
        self.maps_cache = {}
        self.load_maps_cache()
        
        # Initialize threading components
        self.lock = threading.RLock()
        self.refresh_thread = None
        self.running = False
        
        self.console.info(f"Initialized query maps manager with cache at {self.cache_dir}")
    
    def start(self) -> None:
        """
        Start the background refresh thread.
        
        Returns:
            None
        """
        with self.lock:
            if not self.running:
                self.running = True
                self.refresh_thread = threading.Thread(
                    target=self._run_refresh,
                    daemon=True
                )
                self.refresh_thread.start()
                self.console.debug("Started query maps refresh thread")
    
    def stop(self) -> None:
        """
        Stop the background refresh thread.
        
        Returns:
            None
        """
        with self.lock:
            self.running = False
            self.console.debug("Stopped query maps refresh thread")
    
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
        try:
            # Validate parameters
            if not module:
                raise ValueError("Module name cannot be empty")
            if not storage_item:
                raise ValueError("Storage item name cannot be empty")
            
            # Create cache key
            cache_key = f"{module}.{storage_item}"
            
            # Check if we have the map in memory cache
            with self.lock:
                if cache_key in self.maps_cache:
                    self.console.debug(f"Using memory-cached query map for {cache_key}")
                    return self.maps_cache[cache_key]["map"]
            
            # Check if we have the map in file cache
            cache_file = self._get_cache_file_path(module, storage_item)
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        
                        # Check if the cache is still valid
                        if time.time() - data.get("timestamp", 0) < self.refresh_interval:
                            # Store in memory cache
                            with self.lock:
                                self.maps_cache[cache_key] = {
                                    "map": data["map"],
                                    "timestamp": data["timestamp"]
                                }
                            
                            self.console.debug(f"Using file-cached query map for {cache_key}")
                            return data["map"]
                except Exception as e:
                    self.console.warning(f"Failed to load query map from cache: {str(e)}")
            
            # If we get here, we need to fetch the map from the blockchain
            query_map = self._fetch_query_map(module, storage_item)
            
            # Store in memory cache
            with self.lock:
                self.maps_cache[cache_key] = {
                    "map": query_map,
                    "timestamp": time.time()
                }
            
            # Store in file cache
            self._save_query_map_to_cache(module, storage_item, query_map)
            
            return query_map
            
        except Exception as e:
            self.console.error(f"Error getting query map: {str(e)}")
            raise RuntimeError(f"Failed to get query map: {str(e)}")
    
    def refresh_query_maps(self) -> None:
        """
        Refresh all cached query maps.
        
        Returns:
            None
            
        Raises:
            RuntimeError: If refresh fails.
        """
        try:
            # Get all cached maps
            with self.lock:
                cached_maps = list(self.maps_cache.keys())
            
            # Refresh each map
            for cache_key in cached_maps:
                try:
                    # Parse the cache key
                    parts = cache_key.split(".")
                    if len(parts) != 2:
                        self.console.warning(f"Invalid cache key format: {cache_key}")
                        continue
                    
                    module, storage_item = parts
                    
                    # Fetch the map from the blockchain
                    query_map = self._fetch_query_map(module, storage_item)
                    
                    # Update memory cache
                    with self.lock:
                        self.maps_cache[cache_key] = {
                            "map": query_map,
                            "timestamp": time.time()
                        }
                    
                    # Update file cache
                    self._save_query_map_to_cache(module, storage_item, query_map)
                    
                    self.console.debug(f"Refreshed query map for {cache_key}")
                except Exception as e:
                    self.console.error(f"Failed to refresh query map {cache_key}: {str(e)}")
            
            self.console.info(f"Refreshed {len(cached_maps)} query maps")
            
        except Exception as e:
            self.console.error(f"Error refreshing query maps: {str(e)}")
            raise RuntimeError(f"Failed to refresh query maps: {str(e)}")
    
    def load_maps_cache(self) -> None:
        """
        Load all cached query maps into memory.
        
        Returns:
            None
        """
        try:
            # Get all cache files
            if not self.cache_dir.exists():
                return
            
            cache_files = list(self.cache_dir.glob("*.json"))
            
            # Load each file
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        
                        # Extract module and storage item from filename
                        filename = cache_file.stem
                        parts = filename.split(".")
                        if len(parts) != 2:
                            self.console.warning(f"Invalid cache file name format: {filename}")
                            continue
                        
                        module, storage_item = parts
                        cache_key = f"{module}.{storage_item}"
                        
                        # Store in memory cache
                        with self.lock:
                            self.maps_cache[cache_key] = {
                                "map": data["map"],
                                "timestamp": data["timestamp"]
                            }
                except Exception as e:
                    self.console.warning(f"Failed to load query map from {cache_file}: {str(e)}")
            
            self.console.debug(f"Loaded {len(self.maps_cache)} query maps from cache")
            
        except Exception as e:
            self.console.error(f"Error loading maps cache: {str(e)}")
            # Initialize empty dict if loading fails
            self.maps_cache = {}
    
    def _fetch_query_map(self, module: str, storage_item: str) -> Dict[str, Any]:
        """
        Fetch a query map from the blockchain.
        
        Args:
            module (str): The module containing the storage item.
            storage_item (str): The storage item to get the query map for.
            
        Returns:
            Dict[str, Any]: The query map.
            
        Raises:
            RuntimeError: If retrieval fails.
        """
        try:
            # Ensure client is connected
            if not self.client.is_connected():
                self.client.connect()
            
            # Get the substrate interface from the client
            substrate = self._get_substrate_interface()
            
            # Fetch the query map
            self.console.debug(f"Fetching query map for {module}.{storage_item}")
            
            # Get the metadata
            metadata = substrate.get_metadata()
            
            # Find the module
            module_metadata = None
            for pallet in metadata.pallets:
                if pallet.name.lower() == module.lower():
                    module_metadata = pallet
                    break
            
            if not module_metadata:
                raise ValueError(f"Module {module} not found in metadata")
            
            # Find the storage item
            storage_item_metadata = None
            if module_metadata.storage:
                for item in module_metadata.storage.entries:
                    if item.name.lower() == storage_item.lower():
                        storage_item_metadata = item
                        break
            
            if not storage_item_metadata:
                raise ValueError(f"Storage item {storage_item} not found in module {module}")
            
            # Extract the query map
            query_map = {
                "name": storage_item_metadata.name,
                "modifier": storage_item_metadata.modifier,
                "type": storage_item_metadata.type,
                "default": storage_item_metadata.default,
                "documentation": storage_item_metadata.documentation,
                "key_type": None,
                "value_type": None
            }
            
            # Extract type information
            if hasattr(storage_item_metadata, "type"):
                if storage_item_metadata.type.is_map:
                    query_map["key_type"] = storage_item_metadata.type.key
                    query_map["value_type"] = storage_item_metadata.type.value
                elif storage_item_metadata.type.is_double_map:
                    query_map["key1_type"] = storage_item_metadata.type.key1
                    query_map["key2_type"] = storage_item_metadata.type.key2
                    query_map["value_type"] = storage_item_metadata.type.value
                elif storage_item_metadata.type.is_plain:
                    query_map["value_type"] = storage_item_metadata.type.value
            
            return query_map
            
        except SubstrateRequestException as e:
            self.console.error(f"Substrate request error: {str(e)}")
            raise RuntimeError(f"Failed to fetch query map: {str(e)}")
        except Exception as e:
            self.console.error(f"Error fetching query map: {str(e)}")
            raise RuntimeError(f"Failed to fetch query map: {str(e)}")
    
    def _save_query_map_to_cache(self, module: str, storage_item: str, query_map: Dict[str, Any]) -> None:
        """
        Save a query map to the file cache.
        
        Args:
            module (str): The module containing the storage item.
            storage_item (str): The storage item to save the query map for.
            query_map (Dict[str, Any]): The query map to save.
            
        Returns:
            None
        """
        try:
            # Create cache file path
            cache_file = self._get_cache_file_path(module, storage_item)
            
            # Create cache data
            cache_data = {
                "map": query_map,
                "timestamp": time.time()
            }
            
            # Save to file
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            self.console.debug(f"Saved query map for {module}.{storage_item} to {cache_file}")
            
        except Exception as e:
            self.console.error(f"Failed to save query map to cache: {str(e)}")
    
    def _get_cache_file_path(self, module: str, storage_item: str) -> Path:
        """
        Get the cache file path for a query map.
        
        Args:
            module (str): The module containing the storage item.
            storage_item (str): The storage item to get the cache file path for.
            
        Returns:
            Path: The cache file path.
        """
        # Sanitize module and storage item names for filename
        module = module.replace("/", "_").replace("\\", "_")
        storage_item = storage_item.replace("/", "_").replace("\\", "_")
        
        # Create filename
        filename = f"{module}.{storage_item}.json"
        
        # Return full path
        return self.cache_dir / filename
    
    def _run_refresh(self) -> None:
        """
        Run the background refresh in a loop.
        
        This method is intended to be run in a separate thread.
        
        Returns:
            None
        """
        while self.running:
            try:
                # Refresh all query maps
                self.refresh_query_maps()
                
                # Sleep until next refresh
                time.sleep(self.refresh_interval)
            except Exception as e:
                self.console.error(f"Error in refresh thread: {str(e)}")
                # Sleep for a short time to avoid tight loop on error
                time.sleep(60.0)
    
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
