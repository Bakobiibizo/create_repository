"""
Environment Manager for the ComAI Client.

This module provides a centralized environment management system for the ComAI Client,
ensuring consistent access to environment variables and configuration settings.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast
from enum import Enum, auto

from dotenv import load_dotenv

from .singleton import Singleton
from .exceptions import (
    EnvironmentError, 
    EnvironmentVariableNotFoundError, 
    EnvironmentVariableValidationError,
    EnvironmentLoadError
)
from .validation import (
    validate_env_var_type,
    validate_env_var_pattern,
    validate_env_var_options
)
from .path_manager import get_path_manager

T = TypeVar('T')


class EnvironmentType(Enum):
    """Enum representing different environment types."""
    DEVELOPMENT = auto()
    TESTING = auto()
    PRODUCTION = auto()
    
    @classmethod
    def from_string(cls, value: str) -> 'EnvironmentType':
        """
        Convert a string to an EnvironmentType.
        
        Args:
            value: The string value to convert.
            
        Returns:
            The corresponding EnvironmentType.
            
        Raises:
            ValueError: If the value is not a valid environment type.
        """
        value_upper = value.upper()
        for env_type in cls:
            if env_type.name == value_upper:
                return env_type
        
        valid_types = [env_type.name for env_type in cls]
        raise ValueError(f"Invalid environment type: {value}. Valid types are: {valid_types}")


class EnvironmentManager(metaclass=Singleton):
    """
    Centralized environment management for the ComAI Client.
    
    This class provides a registry of environment variables used throughout the application,
    with methods for registering, resolving, and validating environment variables.
    """
    
    def __init__(self) -> None:
        """Initialize the EnvironmentManager with an empty registry."""
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._loaded_files: List[str] = []
        self._env_type: Optional[EnvironmentType] = None
        
        # Load environment variables from .env files
        self._load_env_files()
        
        # Determine the environment type
        self._determine_env_type()
        
        # Register common environment variables
        self._register_common_vars()
    
    def _load_env_files(self) -> None:
        """
        Load environment variables from .env files.
        
        Looks for .env files in the project root and config directory.
        """
        path_manager = get_path_manager()
        
        # Define potential .env file locations
        env_files = [
            path_manager.resolve_path("project_root") / ".env",
            path_manager.resolve_path("config_dir") / ".env",
        ]
        
        # Try to determine the environment type from ENV or ENVIRONMENT variable
        env_name = os.environ.get("ENV") or os.environ.get("ENVIRONMENT")
        if env_name:
            # Also look for environment-specific .env files
            env_files.extend([
                path_manager.resolve_path("project_root") / f".env.{env_name.lower()}",
                path_manager.resolve_path("config_dir") / f".env.{env_name.lower()}",
            ])
        
        # Load each .env file if it exists
        for env_file in env_files:
            if env_file.exists() and env_file.is_file():
                try:
                    load_dotenv(dotenv_path=str(env_file), override=True)
                    self._loaded_files.append(str(env_file))
                except Exception as e:
                    raise EnvironmentLoadError(f"Failed to load environment file {env_file}: {str(e)}")
    
    def _determine_env_type(self) -> None:
        """
        Determine the environment type from environment variables.
        
        Looks for ENV or ENVIRONMENT variable to determine the environment type.
        Defaults to DEVELOPMENT if not specified.
        """
        env_name = os.environ.get("ENV") or os.environ.get("ENVIRONMENT")
        if env_name:
            try:
                self._env_type = EnvironmentType.from_string(env_name)
            except ValueError:
                # Default to development if the environment type is invalid
                self._env_type = EnvironmentType.DEVELOPMENT
        else:
            # Default to development if no environment type is specified
            self._env_type = EnvironmentType.DEVELOPMENT
    
    def _register_common_vars(self) -> None:
        """Register common environment variables with default values."""
        # Register environment type
        self.register_var(
            "ENVIRONMENT",
            default=self._env_type.name if self._env_type else "DEVELOPMENT",
            description="The current environment type (DEVELOPMENT, TESTING, PRODUCTION)"
        )
        
        # Register log level
        self.register_var(
            "LOG_LEVEL",
            default="INFO",
            description="The log level for the application",
            options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        
        # Register application name
        self.register_var(
            "APP_NAME",
            default="comai-client",
            description="The name of the application"
        )
    
    def register_var(self, name: str, default: Optional[str] = None, 
                    description: Optional[str] = None, required: bool = False,
                    pattern: Optional[str] = None, options: Optional[List[str]] = None) -> None:
        """
        Register an environment variable with the given name and metadata.
        
        Args:
            name: The name of the environment variable.
            default: The default value if the variable is not set.
            description: A description of the variable.
            required: Whether the variable is required.
            pattern: A regular expression pattern the variable must match.
            options: A list of valid options for the variable.
            
        Raises:
            ValueError: If the name is invalid.
            EnvironmentVariableValidationError: If the variable is required but not set,
                or if it doesn't match the pattern or options.
        """
        if not name:
            raise ValueError("Environment variable name cannot be empty")
        
        # Store the variable metadata in the registry
        self._registry[name] = {
            "default": default,
            "description": description,
            "required": required,
            "pattern": pattern,
            "options": options
        }
        
        # Validate the variable if it's required
        if required and not self.has_var(name):
            raise EnvironmentVariableValidationError(
                f"Required environment variable '{name}' is not set"
            )
        
        # Validate the variable if it's set
        if self.has_var(name):
            value = os.environ[name]
            
            # Validate pattern if specified
            if pattern:
                validate_env_var_pattern(value, pattern, name)
            
            # Validate options if specified
            if options:
                validate_env_var_options(value, options, name)
    
    def has_var(self, name: str) -> bool:
        """
        Check if an environment variable is set.
        
        Args:
            name: The name of the environment variable.
            
        Returns:
            True if the variable is set, False otherwise.
        """
        return name in os.environ
    
    def get_var(self, name: str, default: Optional[str] = None) -> str:
        """
        Get the value of an environment variable.
        
        Args:
            name: The name of the environment variable.
            default: The default value if the variable is not set.
                If not specified, the default from registration is used.
                
        Returns:
            The value of the environment variable.
            
        Raises:
            EnvironmentVariableNotFoundError: If the variable is not set and no default is provided.
        """
        # Check if the variable is set
        if name in os.environ:
            return os.environ[name]
        
        # Check if the variable is registered with a default
        if name in self._registry and self._registry[name]["default"] is not None:
            return cast(str, self._registry[name]["default"])
        
        # Use the provided default
        if default is not None:
            return default
        
        # Variable not found
        raise EnvironmentVariableNotFoundError(f"Environment variable '{name}' not found")
    
    def get_var_as(self, name: str, type_func: Type[T], default: Optional[T] = None) -> T:
        """
        Get the value of an environment variable converted to a specific type.
        
        Args:
            name: The name of the environment variable.
            type_func: The type to convert the variable to.
            default: The default value if the variable is not set.
                
        Returns:
            The value of the environment variable converted to the specified type.
            
        Raises:
            EnvironmentVariableNotFoundError: If the variable is not set and no default is provided.
            EnvironmentVariableValidationError: If the variable cannot be converted to the specified type.
        """
        # If a default is provided and the variable is not set, return the default
        if not self.has_var(name) and default is not None:
            return default
        
        # Get the variable as a string
        value = self.get_var(name)
        
        # Convert to the specified type
        return validate_env_var_type(value, type_func, name)
    
    def get_var_as_bool(self, name: str, default: Optional[bool] = None) -> bool:
        """
        Get the value of an environment variable as a boolean.
        
        Args:
            name: The name of the environment variable.
            default: The default value if the variable is not set.
                
        Returns:
            The value of the environment variable as a boolean.
            
        Raises:
            EnvironmentVariableNotFoundError: If the variable is not set and no default is provided.
            EnvironmentVariableValidationError: If the variable cannot be converted to a boolean.
        """
        # If a default is provided and the variable is not set, return the default
        if not self.has_var(name) and default is not None:
            return default
        
        # Get the variable as a string
        value = self.get_var(name).lower()
        
        # Convert to boolean
        if value in ("true", "yes", "1", "y", "t"):
            return True
        elif value in ("false", "no", "0", "n", "f"):
            return False
        else:
            raise EnvironmentVariableValidationError(
                f"Environment variable '{name}' value '{value}' cannot be converted to boolean"
            )
    
    def get_var_as_int(self, name: str, default: Optional[int] = None) -> int:
        """
        Get the value of an environment variable as an integer.
        
        Args:
            name: The name of the environment variable.
            default: The default value if the variable is not set.
                
        Returns:
            The value of the environment variable as an integer.
            
        Raises:
            EnvironmentVariableNotFoundError: If the variable is not set and no default is provided.
            EnvironmentVariableValidationError: If the variable cannot be converted to an integer.
        """
        return self.get_var_as(name, int, default)
    
    def get_var_as_float(self, name: str, default: Optional[float] = None) -> float:
        """
        Get the value of an environment variable as a float.
        
        Args:
            name: The name of the environment variable.
            default: The default value if the variable is not set.
                
        Returns:
            The value of the environment variable as a float.
            
        Raises:
            EnvironmentVariableNotFoundError: If the variable is not set and no default is provided.
            EnvironmentVariableValidationError: If the variable cannot be converted to a float.
        """
        return self.get_var_as(name, float, default)
    
    def get_var_as_list(self, name: str, separator: str = ",", 
                       default: Optional[List[str]] = None) -> List[str]:
        """
        Get the value of an environment variable as a list of strings.
        
        Args:
            name: The name of the environment variable.
            separator: The separator to split the variable value.
            default: The default value if the variable is not set.
                
        Returns:
            The value of the environment variable as a list of strings.
            
        Raises:
            EnvironmentVariableNotFoundError: If the variable is not set and no default is provided.
        """
        # If a default is provided and the variable is not set, return the default
        if not self.has_var(name) and default is not None:
            return default
        
        # Get the variable as a string
        value = self.get_var(name)
        
        # Split into a list
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    def get_var_as_dict(self, name: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the value of an environment variable as a dictionary.
        
        The variable value should be a JSON-encoded string.
        
        Args:
            name: The name of the environment variable.
            default: The default value if the variable is not set.
                
        Returns:
            The value of the environment variable as a dictionary.
            
        Raises:
            EnvironmentVariableNotFoundError: If the variable is not set and no default is provided.
            EnvironmentVariableValidationError: If the variable cannot be converted to a dictionary.
        """
        # If a default is provided and the variable is not set, return the default
        if not self.has_var(name) and default is not None:
            return default
        
        # Get the variable as a string
        value = self.get_var(name)
        
        # Convert to a dictionary
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise EnvironmentVariableValidationError(
                f"Environment variable '{name}' value '{value}' is not valid JSON: {str(e)}"
            )
    
    def set_var(self, name: str, value: str) -> None:
        """
        Set the value of an environment variable.
        
        This only sets the variable in the current process, not in the system environment.
        
        Args:
            name: The name of the environment variable.
            value: The value to set.
            
        Raises:
            EnvironmentVariableValidationError: If the variable is registered with a pattern or options
                and the value doesn't match.
        """
        # Validate the value if the variable is registered
        if name in self._registry:
            # Validate pattern if specified
            pattern = self._registry[name]["pattern"]
            if pattern:
                validate_env_var_pattern(value, pattern, name)
            
            # Validate options if specified
            options = self._registry[name]["options"]
            if options:
                validate_env_var_options(value, options, name)
        
        # Set the variable
        os.environ[name] = value
    
    def get_env_type(self) -> EnvironmentType:
        """
        Get the current environment type.
        
        Returns:
            The current environment type.
        """
        if self._env_type is None:
            self._determine_env_type()
        
        return cast(EnvironmentType, self._env_type)
    
    def is_development(self) -> bool:
        """
        Check if the current environment is development.
        
        Returns:
            True if the current environment is development, False otherwise.
        """
        return self.get_env_type() == EnvironmentType.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """
        Check if the current environment is testing.
        
        Returns:
            True if the current environment is testing, False otherwise.
        """
        return self.get_env_type() == EnvironmentType.TESTING
    
    def is_production(self) -> bool:
        """
        Check if the current environment is production.
        
        Returns:
            True if the current environment is production, False otherwise.
        """
        return self.get_env_type() == EnvironmentType.PRODUCTION
    
    def get_registered_vars(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a dictionary of all registered environment variables.
        
        Returns:
            A dictionary mapping variable names to their metadata.
        """
        return self._registry.copy()
    
    def get_loaded_files(self) -> List[str]:
        """
        Get a list of all loaded environment files.
        
        Returns:
            A list of file paths that were loaded.
        """
        return self._loaded_files.copy()


def get_environment_manager() -> EnvironmentManager:
    """
    Get the singleton instance of the EnvironmentManager.
    
    Returns:
        The EnvironmentManager instance.
    """
    return EnvironmentManager()
