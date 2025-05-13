"""
Test script for interacting with a live blockchain node.

This script demonstrates the usage of the SubstrateClient and ConnectionManager
classes to interact with a running blockchain node.
"""

import logging
import time
from typing import Dict, Any

from blockchain_interface.client import SubstrateClient
from blockchain_interface.connection import ConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_substrate_client():
    """Test the SubstrateClient with a live node."""
    url = "ws://localhost:9944"
    
    logger.info(f"Testing SubstrateClient with node at {url}")
    
    try:
        # Test connection
        with SubstrateClient(url) as client:
            logger.info("Connected to node")
            
            # Test system RPC calls
            system_name = client.execute_rpc("system_name", [])
            logger.info(f"System name: {system_name}")
            
            system_health = client.execute_rpc("system_health", [])
            logger.info(f"System health: {system_health}")
            
            system_chain = client.execute_rpc("system_chain", [])
            logger.info(f"System chain: {system_chain}")
            
            # Test runtime metadata
            runtime_metadata = client.execute_rpc("state_getMetadata", [])
            logger.info(f"Runtime metadata received: {len(str(runtime_metadata))} bytes")
            
        logger.info("Disconnected from node")
        
    except Exception as e:
        logger.error(f"Error testing SubstrateClient: {str(e)}")
        raise


def test_connection_manager():
    """Test the ConnectionManager with a live node."""
    url = "ws://localhost:9944"
    
    logger.info(f"Testing ConnectionManager with node at {url}")
    
    try:
        # Create and start connection manager
        with ConnectionManager(url, max_connections=3, idle_timeout=10.0, heartbeat_interval=5.0) as manager:
            logger.info("Connection manager started")
            
            # Get multiple connections and perform operations
            connections = []
            for i in range(3):
                conn_id, conn = manager.get_connection()
                connections.append((conn_id, conn))
                logger.info(f"Got connection {conn_id}")
                
                # Test connection with a simple RPC call
                result = conn.rpc_request("system_name", [])
                logger.info(f"Connection {conn_id} - System name: {result}")
            
            # Release one connection
            if connections:
                conn_id, _ = connections.pop()
                logger.info(f"Releasing connection {conn_id}")
                manager.release_connection(conn_id)
                
                # Get another connection (should reuse the released one)
                new_conn_id, new_conn = manager.get_connection()
                logger.info(f"Got connection {new_conn_id}")
                result = new_conn.rpc_request("system_chain", [])
                logger.info(f"Connection {new_conn_id} - System chain: {result}")
                
                # Release all connections
                manager.release_connection(new_conn_id)
                for conn_id, _ in connections:
                    manager.release_connection(conn_id)
            
            # Let the heartbeat run for a while
            logger.info("Waiting for heartbeat to run...")
            time.sleep(15)
            
        logger.info("Connection manager stopped")
        
    except Exception as e:
        logger.error(f"Error testing ConnectionManager: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Test SubstrateClient
        test_substrate_client()
        
        # Test ConnectionManager
        test_connection_manager()
        
        logger.info("All tests completed successfully")
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
