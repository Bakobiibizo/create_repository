"""
Extrinsics Handler for ComAI Client.

This module provides functionality for submitting and tracking blockchain extrinsics.
It handles parameter validation, transaction submission, and status tracking.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union
import json

from substrateinterface import SubstrateInterface, Keypair, ExtrinsicReceipt
from substrateinterface.exceptions import SubstrateRequestException

from src.utilities.environment_manager import get_environment_manager
from src.utilities.path_manager import get_path_manager
from src.utilities.console_manager import get_console_manager
from src.blockchain_interface.interfaces import ExtrinsicsHandlerInterface
from src.blockchain_interface.client import SubstrateClient

logger = logging.getLogger(__name__)


class ExtrinsicsHandler(ExtrinsicsHandlerInterface):
    """
    Handles blockchain extrinsics for the ComAI Client.
    
    This class implements the ExtrinsicsHandlerInterface and provides methods for submitting
    extrinsics to the blockchain and tracking their status.
    
    Attributes:
        client (SubstrateClient): The blockchain client to use for extrinsic submission.
        pending_extrinsics (Dict): Dictionary of pending extrinsics and their metadata.
        status_check_interval (float): Interval in seconds between status checks.
    """
    
    def __init__(
        self,
        client: Optional[SubstrateClient] = None,
        status_check_interval: Optional[float] = None,
        config_path: Optional[str] = None
    ):
        """
        Initialize a new ExtrinsicsHandler.
        
        Args:
            client (Optional[SubstrateClient], optional): The blockchain client to use.
                If not provided, a new client will be created.
            status_check_interval (Optional[float], optional): Interval in seconds between status checks.
                If not provided, it will be read from the environment variable BLOCKCHAIN_STATUS_CHECK_INTERVAL.
                Defaults to 2.0.
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
        
        # Get status check interval from environment if not provided
        self.status_check_interval = status_check_interval if status_check_interval is not None else env_manager.get_var_as_float("BLOCKCHAIN_STATUS_CHECK_INTERVAL", 2.0)
        
        # Initialize client
        self.client = client
        if self.client is None:
            self.client = SubstrateClient()
            if not self.client.is_connected():
                self.client.connect()
        
        # Initialize pending extrinsics
        self.pending_extrinsics = {}
        
        self.console.info("Initialized extrinsics handler")
    
    def submit_extrinsic(
        self, 
        module: str, 
        call: str, 
        params: Dict[str, Any], 
        account: Union[Keypair, Dict[str, Any]]
    ) -> str:
        """
        Submit an extrinsic to the blockchain.
        
        Args:
            module (str): The module containing the call.
            call (str): The call to execute.
            params (Dict[str, Any]): Parameters for the call.
            account (Union[Keypair, Dict[str, Any]]): The account to sign the extrinsic.
                Can be a Keypair object or a dictionary with 'seed' or 'mnemonic' key.
            
        Returns:
            str: The hash of the submitted extrinsic.
            
        Raises:
            ValueError: If parameters are invalid.
            RuntimeError: If submission fails.
        """
        try:
            # Validate parameters
            if not module:
                raise ValueError("Module name cannot be empty")
            if not call:
                raise ValueError("Call name cannot be empty")
            
            # Ensure client is connected
            if not self.client.is_connected():
                self.client.connect()
            
            # Convert account to Keypair if necessary
            keypair = self._get_keypair(account)
            
            # Get the substrate interface from the client
            substrate = self._get_substrate_interface()
            
            # Submit the extrinsic
            self.console.info(f"Submitting extrinsic: {module}.{call} with params: {json.dumps(params, default=str)}")
            
            # Create the call
            call = substrate.compose_call(
                call_module=module,
                call_function=call,
                call_params=params
            )
            
            # Create the extrinsic
            extrinsic = substrate.create_signed_extrinsic(
                call=call,
                keypair=keypair
            )
            
            # Submit the extrinsic
            receipt = substrate.submit_extrinsic(
                extrinsic=extrinsic,
                wait_for_inclusion=False
            )
            
            # Store the pending extrinsic
            extrinsic_hash = receipt.extrinsic_hash
            self.pending_extrinsics[extrinsic_hash] = {
                "receipt": receipt,
                "module": module,
                "call": call,
                "params": params,
                "submitted_at": time.time(),
                "status": "submitted"
            }
            
            self.console.info(f"Extrinsic submitted with hash: {extrinsic_hash}")
            return extrinsic_hash
            
        except SubstrateRequestException as e:
            self.console.error(f"Substrate request error: {str(e)}")
            raise RuntimeError(f"Failed to submit extrinsic: {str(e)}")
        except Exception as e:
            self.console.error(f"Error submitting extrinsic: {str(e)}")
            raise RuntimeError(f"Failed to submit extrinsic: {str(e)}")
    
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
        try:
            # Validate hash
            if not extrinsic_hash:
                raise ValueError("Extrinsic hash cannot be empty")
            
            # Check if we have the extrinsic in our pending list
            if extrinsic_hash in self.pending_extrinsics:
                # Get the receipt
                receipt = self.pending_extrinsics[extrinsic_hash]["receipt"]
                
                # Update the status
                try:
                    updated_receipt = receipt.update_result()
                    
                    # Update our stored receipt
                    self.pending_extrinsics[extrinsic_hash]["receipt"] = updated_receipt
                    
                    # Check if the extrinsic is in a block
                    if updated_receipt.is_success:
                        self.pending_extrinsics[extrinsic_hash]["status"] = "success"
                        self.console.info(f"Extrinsic {extrinsic_hash} succeeded in block {updated_receipt.block_hash}")
                    elif updated_receipt.error_message:
                        self.pending_extrinsics[extrinsic_hash]["status"] = "error"
                        self.pending_extrinsics[extrinsic_hash]["error"] = updated_receipt.error_message
                        self.console.error(f"Extrinsic {extrinsic_hash} failed: {updated_receipt.error_message}")
                    else:
                        self.pending_extrinsics[extrinsic_hash]["status"] = "pending"
                        
                except Exception as e:
                    # If we can't update the receipt, assume it's still pending
                    self.console.warning(f"Failed to update receipt for {extrinsic_hash}: {str(e)}")
                
                # Return the status
                return {
                    "hash": extrinsic_hash,
                    "status": self.pending_extrinsics[extrinsic_hash]["status"],
                    "submitted_at": self.pending_extrinsics[extrinsic_hash]["submitted_at"],
                    "block_hash": receipt.block_hash if receipt.block_hash else None,
                    "block_number": receipt.block_number if receipt.block_number else None,
                    "error": self.pending_extrinsics[extrinsic_hash].get("error")
                }
            
            # If we don't have the extrinsic in our pending list, query the blockchain
            substrate = self._get_substrate_interface()
            
            # Query the blockchain for the extrinsic
            result = substrate.get_runtime_state(
                module="System",
                storage_function="Events",
                params=[]
            )
            
            # Parse the events to find our extrinsic
            if result and "result" in result:
                events = substrate.process_events(result["result"])
                for event in events:
                    if hasattr(event, "extrinsic_hash") and event.extrinsic_hash == extrinsic_hash:
                        # Found the extrinsic
                        return {
                            "hash": extrinsic_hash,
                            "status": "success" if not hasattr(event, "error") else "error",
                            "block_hash": event.block_hash if hasattr(event, "block_hash") else None,
                            "block_number": event.block_number if hasattr(event, "block_number") else None,
                            "error": event.error if hasattr(event, "error") else None
                        }
            
            # If we can't find the extrinsic, return unknown status
            return {
                "hash": extrinsic_hash,
                "status": "unknown"
            }
            
        except Exception as e:
            self.console.error(f"Error getting extrinsic status: {str(e)}")
            raise RuntimeError(f"Failed to get extrinsic status: {str(e)}")
    
    def wait_for_extrinsic(
        self, 
        extrinsic_hash: str, 
        timeout: float = 60.0,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Wait for an extrinsic to be included in a block.
        
        Args:
            extrinsic_hash (str): The hash of the extrinsic.
            timeout (float, optional): Maximum time to wait in seconds.
                Defaults to 60.0.
            callback (Optional[Callable[[Dict[str, Any]], None]], optional): Callback function to call when status changes.
                Defaults to None.
                
        Returns:
            Dict[str, Any]: The final status of the extrinsic.
            
        Raises:
            ValueError: If the hash is invalid.
            TimeoutError: If the timeout is reached.
            RuntimeError: If status retrieval fails.
        """
        try:
            # Validate hash
            if not extrinsic_hash:
                raise ValueError("Extrinsic hash cannot be empty")
            
            # Track start time
            start_time = time.time()
            
            # Track last status
            last_status = None
            
            # Wait for the extrinsic to be included
            while time.time() - start_time < timeout:
                # Get the status
                status = self.get_extrinsic_status(extrinsic_hash)
                
                # Call the callback if status changed
                if callback and status != last_status:
                    callback(status)
                
                # Update last status
                last_status = status
                
                # Check if the extrinsic is finalized
                if status["status"] in ["success", "error"]:
                    return status
                
                # Sleep before checking again
                time.sleep(self.status_check_interval)
            
            # If we get here, we timed out
            raise TimeoutError(f"Timed out waiting for extrinsic {extrinsic_hash} after {timeout} seconds")
            
        except TimeoutError:
            # Re-raise timeout errors
            raise
        except Exception as e:
            self.console.error(f"Error waiting for extrinsic: {str(e)}")
            raise RuntimeError(f"Failed to wait for extrinsic: {str(e)}")
    
    def _get_keypair(self, account: Union[Keypair, Dict[str, Any]]) -> Keypair:
        """
        Get a Keypair from an account.
        
        Args:
            account (Union[Keypair, Dict[str, Any]]): The account to get a Keypair for.
                Can be a Keypair object or a dictionary with 'seed' or 'mnemonic' key.
                
        Returns:
            Keypair: The Keypair for the account.
            
        Raises:
            ValueError: If the account is invalid.
        """
        if isinstance(account, Keypair):
            return account
        
        if isinstance(account, dict):
            if "seed" in account:
                return Keypair.create_from_seed(account["seed"])
            elif "mnemonic" in account:
                return Keypair.create_from_mnemonic(account["mnemonic"])
            elif "uri" in account:
                return Keypair.create_from_uri(account["uri"])
        
        raise ValueError("Invalid account. Must be a Keypair or a dictionary with 'seed', 'mnemonic', or 'uri' key.")
    
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
