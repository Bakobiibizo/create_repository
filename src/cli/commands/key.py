"""
Key commands for the ComAI Client CLI.

This module provides commands for managing cryptographic keys.
"""

import typer
from typing import Optional
from rich.console import Console

from src.cli.common import format_output, get_global_context

# Initialize console
console = Console()

# Create the key app
app = typer.Typer(
    name="key",
    help="Manage cryptographic keys",
    no_args_is_help=True,
)


class KeyManager:
    """Manager for cryptographic keys."""
    
    def __init__(self):
        """Initialize the key manager."""
        from src.utilities.environment_manager import get_environment_manager
        
        self.env_manager = get_environment_manager()
        self.keys_dir = self.env_manager.get_var("COMAI_KEYS_DIR", "~/.comai/keys")
        
        # Ensure keys directory exists
        import os
        import pathlib
        
        keys_path = pathlib.Path(os.path.expanduser(self.keys_dir))
        keys_path.mkdir(parents=True, exist_ok=True)
    
    def list_keys(self):
        """
        List all available keys.
        
        Returns:
            list: List of key information dictionaries.
        """
        import os
        import json
        import pathlib
        
        keys_path = pathlib.Path(os.path.expanduser(self.keys_dir))
        keys = []
        
        for key_file in keys_path.glob("*.json"):
            try:
                with open(key_file, "r") as f:
                    key_data = json.load(f)
                    keys.append({
                        "name": key_file.stem,
                        "address": key_data["address"],
                        "type": key_data["type"]
                    })
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not read key file {key_file}: {str(e)}")
        
        return keys
    
    def generate_key(self, name, key_type="sr25519"):
        """
        Generate a new key.
        
        Args:
            name: Name for the key.
            key_type: Type of key to generate (sr25519, ed25519, or ecdsa).
            
        Returns:
            dict: Generated key information.
        """
        # Validate key type
        if key_type not in ["sr25519", "ed25519", "ecdsa"]:
            raise ValueError(f"Invalid key type: {key_type}. Must be one of: sr25519, ed25519, ecdsa")
        
        # Generate key
        from substrate_interface.key import Keypair
        
        keypair = Keypair.create_from_mnemonic(Keypair.generate_mnemonic(), key_type)
        
        # Save key
        self._save_key(name, keypair, key_type)
        
        # Return key information
        return {
            "name": name,
            "address": keypair.ss58_address,
            "type": key_type,
            "mnemonic": keypair.mnemonic
        }
    
    def import_key(self, name, mnemonic, key_type="sr25519"):
        """
        Import a key from a mnemonic.
        
        Args:
            name: Name for the key.
            mnemonic: Mnemonic phrase.
            key_type: Type of key (sr25519, ed25519, or ecdsa).
            
        Returns:
            dict: Imported key information.
        """
        # Validate key type
        if key_type not in ["sr25519", "ed25519", "ecdsa"]:
            raise ValueError(f"Invalid key type: {key_type}. Must be one of: sr25519, ed25519, ecdsa")
        
        # Create keypair from mnemonic
        from substrate_interface.key import Keypair
        
        try:
            keypair = Keypair.create_from_mnemonic(mnemonic, key_type)
        except Exception as e:
            raise ValueError(f"Invalid mnemonic: {str(e)}")
        
        # Save key
        self._save_key(name, keypair, key_type)
        
        # Return key information
        return {
            "name": name,
            "address": keypair.ss58_address,
            "type": key_type
        }
    
    def export_key(self, name):
        """
        Export a key.
        
        Args:
            name: Name of the key to export.
            
        Returns:
            dict: Key information including mnemonic.
        """
        import os
        import json
        import pathlib
        
        keys_path = pathlib.Path(os.path.expanduser(self.keys_dir))
        key_file = keys_path / f"{name}.json"
        
        if not key_file.exists():
            raise ValueError(f"Key not found: {name}")
        
        try:
            with open(key_file, "r") as f:
                key_data = json.load(f)
                
                return {
                    "name": name,
                    "address": key_data["address"],
                    "type": key_data["type"],
                    "mnemonic": key_data["mnemonic"]
                }
        except Exception as e:
            raise ValueError(f"Could not read key file: {str(e)}")
    
    def delete_key(self, name):
        """
        Delete a key.
        
        Args:
            name: Name of the key to delete.
            
        Returns:
            bool: True if the key was deleted, False otherwise.
        """
        import os
        import pathlib
        
        keys_path = pathlib.Path(os.path.expanduser(self.keys_dir))
        key_file = keys_path / f"{name}.json"
        
        if not key_file.exists():
            raise ValueError(f"Key not found: {name}")
        
        try:
            os.remove(key_file)
            return True
        except Exception as e:
            raise ValueError(f"Could not delete key file: {str(e)}")
    
    def _save_key(self, name, keypair, key_type):
        """
        Save a key to a file.
        
        Args:
            name: Name for the key.
            keypair: Keypair object.
            key_type: Type of key.
        """
        import os
        import json
        import pathlib
        
        keys_path = pathlib.Path(os.path.expanduser(self.keys_dir))
        key_file = keys_path / f"{name}.json"
        
        # Check if key already exists
        if key_file.exists():
            raise ValueError(f"Key already exists: {name}")
        
        # Save key data
        key_data = {
            "address": keypair.ss58_address,
            "type": key_type,
            "mnemonic": keypair.mnemonic,
            "private_key": "0x" + keypair.private_key.hex(),
            "public_key": "0x" + keypair.public_key.hex()
        }
        
        with open(key_file, "w") as f:
            json.dump(key_data, f, indent=2)


@app.command("list")
def list_keys():
    """
    List all available keys.
    
    This command lists all available keys with their addresses and types.
    """
    try:
        # Get key manager
        key_manager = KeyManager()
        
        # List keys
        keys = key_manager.list_keys()
        
        # Format and display the result
        from src.cli.common import get_global_context
        
        if get_global_context().json_output:
            # For JSON output, use the raw keys list without wrapping
            import json
            print(json.dumps(keys, indent=2))
        else:
            # For human-readable output, use the format_output function
            format_output(keys, "Available Keys")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("generate")
def generate_key(
    name: str = typer.Argument(..., help="Name for the key"),
    key_type: str = typer.Option(
        "sr25519", "--type", "-t", help="Type of key (sr25519, ed25519, or ecdsa)"
    )
):
    """
    Generate a new key.
    
    This command generates a new cryptographic key and saves it to the key store.
    The mnemonic phrase is displayed once and should be saved securely.
    """
    try:
        # Get key manager
        key_manager = KeyManager()
        
        # Generate key
        key = key_manager.generate_key(name, key_type)
        
        # Format and display the result
        console.print(f"[bold green]Key generated successfully:[/bold green] {name}")
        console.print(f"Address: {key['address']}")
        console.print(f"Type: {key['type']}")
        console.print(f"[bold yellow]Mnemonic (save this securely):[/bold yellow] {key['mnemonic']}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("import")
def import_key(
    name: str = typer.Argument(..., help="Name for the key"),
    mnemonic: str = typer.Option(
        ..., "--mnemonic", "-m", help="Mnemonic phrase"
    ),
    key_type: str = typer.Option(
        "sr25519", "--type", "-t", help="Type of key (sr25519, ed25519, or ecdsa)"
    )
):
    """
    Import a key from a mnemonic.
    
    This command imports a key from a mnemonic phrase and saves it to the key store.
    """
    try:
        # Get key manager
        key_manager = KeyManager()
        
        # Import key
        key = key_manager.import_key(name, mnemonic, key_type)
        
        # Format and display the result
        console.print(f"[bold green]Key imported successfully:[/bold green] {name}")
        console.print(f"Address: {key['address']}")
        console.print(f"Type: {key['type']}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("export")
def export_key(
    name: str = typer.Argument(..., help="Name of the key to export")
):
    """
    Export a key.
    
    This command exports a key, including its mnemonic phrase.
    The mnemonic phrase should be handled securely.
    """
    try:
        # Get key manager
        key_manager = KeyManager()
        
        # Export key
        key = key_manager.export_key(name)
        
        # Format and display the result
        console.print(f"[bold green]Key exported:[/bold green] {name}")
        console.print(f"Address: {key['address']}")
        console.print(f"Type: {key['type']}")
        console.print(f"[bold yellow]Mnemonic:[/bold yellow] {key['mnemonic']}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("delete")
def delete_key(
    name: str = typer.Argument(..., help="Name of the key to delete"),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    )
):
    """
    Delete a key.
    
    This command deletes a key from the key store.
    """
    try:
        # Confirm deletion
        if not yes:
            confirm = typer.confirm(f"Are you sure you want to delete the key '{name}'?")
            if not confirm:
                console.print("[yellow]Operation cancelled.[/yellow]")
                return
        
        # Get key manager
        key_manager = KeyManager()
        
        # Delete key
        key_manager.delete_key(name)
        
        # Display confirmation
        console.print(f"[bold green]Key deleted:[/bold green] {name}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)
