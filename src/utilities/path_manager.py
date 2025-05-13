"""
Path Manager for the ComAI Client.

This module provides a centralized path management system for the ComAI Client,
ensuring consistent path handling across the application.
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional, Union, Any, List

from .singleton import Singleton
from .exceptions import PathNotFoundError, PathResolutionError, PathValidationError
from .validation import validate_path_exists, validate_directory_exists, validate_file_exists


class PathManager(metaclass=Singleton):
    """
    Centralized path management for the ComAI Client.
    
    This class provides a registry of paths used throughout the application,
    with methods for registering, resolving, and validating paths.
    """
    
    def __init__(self) -> None:
        """Initialize the PathManager with an empty registry."""
        self._registry: Dict[str, str] = {}
        self._cache: Dict[str, Path] = {}
        
        # Register base paths
        self._register_base_paths()
    
    def _register_base_paths(self) -> None:
        """Register base paths that are used throughout the application."""
        # Get the project root directory (assuming this file is in src/utilities)
        current_file = Path(__file__).resolve()
        src_dir = current_file.parent.parent
        project_root = src_dir.parent
        
        # Register base paths
        self.register_path("project_root", str(project_root))
        self.register_path("src_dir", str(src_dir))
        self.register_path("utilities_dir", str(current_file.parent))
        
        # Register common directories
        self.register_path("config_dir", "${project_root}/config")
        self.register_path("data_dir", "${project_root}/data")
        self.register_path("logs_dir", "${project_root}/logs")
        self.register_path("tests_dir", "${project_root}/tests")
        
        # Ensure critical directories exist
        self._ensure_critical_directories()
    
    def _ensure_critical_directories(self) -> None:
        """Ensure critical directories exist, creating them if necessary."""
        critical_dirs = ["config_dir", "data_dir", "logs_dir"]
        
        for dir_name in critical_dirs:
            try:
                dir_path = self.resolve_path(dir_name)
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                # Log the error but don't raise it - we don't want to block initialization
                print(f"Warning: Failed to create critical directory {dir_name}: {str(e)}")
    
    def register_path(self, name: str, path: str) -> None:
        """
        Register a path with the given name.
        
        Args:
            name: The name to register the path under.
            path: The path to register. Can include variable substitutions like ${var_name}.
            
        Raises:
            ValueError: If the name or path is invalid.
        """
        if not name:
            raise ValueError("Path name cannot be empty")
        if not path:
            raise ValueError("Path cannot be empty")
        
        # Store the path in the registry
        self._registry[name] = path
        
        # Clear the cache for this path
        if name in self._cache:
            del self._cache[name]
    
    def resolve_path(self, name_or_path: str, validate: bool = False) -> Path:
        """
        Resolve a path by name or path string.
        
        If the input is a registered path name, the corresponding path is returned.
        If the input is a path string, it is resolved with variable substitution.
        
        Args:
            name_or_path: The path name or path string to resolve.
            validate: Whether to validate that the path exists.
            
        Returns:
            The resolved path as a Path object.
            
        Raises:
            PathNotFoundError: If the path name is not found in the registry.
            PathResolutionError: If the path cannot be resolved.
            PathValidationError: If validate is True and the path does not exist.
        """
        # Check if the path is in the cache
        if name_or_path in self._cache:
            resolved_path = self._cache[name_or_path]
            if validate:
                validate_path_exists(resolved_path)
            return resolved_path
        
        # If the name is in the registry, get the path
        if name_or_path in self._registry:
            path_str = self._registry[name_or_path]
        else:
            # Otherwise, use the input as a path string
            path_str = name_or_path
        
        # Resolve variable substitutions
        resolved_str = self._resolve_variables(path_str)
        
        # Convert to a Path object
        try:
            resolved_path = Path(resolved_str).resolve()
        except Exception as e:
            raise PathResolutionError(f"Failed to resolve path '{name_or_path}': {str(e)}")
        
        # Validate if requested
        if validate:
            validate_path_exists(resolved_path)
        
        # Cache the result
        self._cache[name_or_path] = resolved_path
        
        return resolved_path
    
    def _resolve_variables(self, path_str: str) -> str:
        """
        Resolve variable substitutions in a path string.
        
        Variables are in the format ${var_name} and can refer to registered paths
        or environment variables.
        
        Args:
            path_str: The path string to resolve.
            
        Returns:
            The resolved path string.
            
        Raises:
            PathResolutionError: If a variable cannot be resolved.
        """
        # Find all variables in the path
        var_pattern = r'\${([^}]+)}'
        matches = re.finditer(var_pattern, path_str)
        
        # Replace each variable with its value
        result = path_str
        for match in matches:
            var_name = match.group(1)
            var_ref = match.group(0)  # The full ${var_name}
            
            # Check if the variable is a registered path
            if var_name in self._registry:
                # Recursively resolve the variable
                var_value = self._resolve_variables(self._registry[var_name])
            # Check if the variable is an environment variable
            elif var_name in os.environ:
                var_value = os.environ[var_name]
            else:
                raise PathResolutionError(f"Unknown variable in path: {var_ref}")
            
            # Replace the variable in the path
            result = result.replace(var_ref, var_value)
        
        return result
    
    def get_registered_paths(self) -> Dict[str, str]:
        """
        Get a dictionary of all registered paths.
        
        Returns:
            A dictionary mapping path names to path strings.
        """
        return self._registry.copy()
    
    def clear_cache(self) -> None:
        """Clear the path resolution cache."""
        self._cache.clear()
    
    def resolve_directory(self, name_or_path: str, create: bool = False) -> Path:
        """
        Resolve a path and ensure it is a directory.
        
        Args:
            name_or_path: The path name or path string to resolve.
            create: Whether to create the directory if it doesn't exist.
            
        Returns:
            The resolved directory path as a Path object.
            
        Raises:
            PathNotFoundError: If the path name is not found in the registry.
            PathResolutionError: If the path cannot be resolved.
            PathValidationError: If the path is not a directory.
        """
        path = self.resolve_path(name_or_path)
        
        if path.exists():
            if not path.is_dir():
                raise PathValidationError(f"Path is not a directory: {path}")
        elif create:
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                raise PathValidationError(f"Failed to create directory: {path}: {str(e)}")
        else:
            raise PathValidationError(f"Directory does not exist: {path}")
        
        return path
    
    def resolve_file(self, name_or_path: str, create_parent: bool = False) -> Path:
        """
        Resolve a path and ensure it is a file.
        
        Args:
            name_or_path: The path name or path string to resolve.
            create_parent: Whether to create the parent directory if it doesn't exist.
            
        Returns:
            The resolved file path as a Path object.
            
        Raises:
            PathNotFoundError: If the path name is not found in the registry.
            PathResolutionError: If the path cannot be resolved.
            PathValidationError: If the path is not a file.
        """
        path = self.resolve_path(name_or_path)
        
        if path.exists():
            if not path.is_file():
                raise PathValidationError(f"Path is not a file: {path}")
        elif create_parent:
            try:
                os.makedirs(path.parent, exist_ok=True)
            except Exception as e:
                raise PathValidationError(f"Failed to create parent directory: {path.parent}: {str(e)}")
        
        return path
    
    def join_path(self, base_path: Union[str, Path], *parts: str) -> Path:
        """
        Join a base path with additional parts.
        
        The base path can be a registered path name, a path string, or a Path object.
        
        Args:
            base_path: The base path to join with.
            *parts: Additional path parts to join.
            
        Returns:
            The joined path as a Path object.
            
        Raises:
            PathNotFoundError: If the base path name is not found in the registry.
            PathResolutionError: If the base path cannot be resolved.
        """
        if isinstance(base_path, str):
            base = self.resolve_path(base_path)
        else:
            base = Path(base_path)
        
        return base.joinpath(*parts)
    
    def find_file(self, name: str, search_paths: List[Union[str, Path]], 
                  recursive: bool = False) -> Optional[Path]:
        """
        Find a file by name in a list of search paths.
        
        Args:
            name: The name of the file to find.
            search_paths: A list of paths to search in.
            recursive: Whether to search recursively.
            
        Returns:
            The path to the file if found, or None if not found.
        """
        for search_path in search_paths:
            path = self.resolve_path(search_path)
            if not path.exists() or not path.is_dir():
                continue
            
            if recursive:
                for root, _, files in os.walk(path):
                    if name in files:
                        return Path(root) / name
            else:
                file_path = path / name
                if file_path.exists() and file_path.is_file():
                    return file_path
        
        return None
    
    def find_directory(self, name: str, search_paths: List[Union[str, Path]], 
                       recursive: bool = False) -> Optional[Path]:
        """
        Find a directory by name in a list of search paths.
        
        Args:
            name: The name of the directory to find.
            search_paths: A list of paths to search in.
            recursive: Whether to search recursively.
            
        Returns:
            The path to the directory if found, or None if not found.
        """
        for search_path in search_paths:
            path = self.resolve_path(search_path)
            if not path.exists() or not path.is_dir():
                continue
            
            if recursive:
                for root, dirs, _ in os.walk(path):
                    if name in dirs:
                        return Path(root) / name
            else:
                dir_path = path / name
                if dir_path.exists() and dir_path.is_dir():
                    return dir_path
        
        return None
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """
        Normalize a path to an absolute path.
        
        Args:
            path: The path to normalize.
            
        Returns:
            The normalized path as a Path object.
        """
        if isinstance(path, str):
            # If the path is a registered name, resolve it
            if path in self._registry:
                return self.resolve_path(path)
            
            # If the path contains variables, resolve them
            if '${' in path:
                resolved_str = self._resolve_variables(path)
                return Path(resolved_str).resolve()
            
            # Otherwise, convert to a Path and resolve
            return Path(path).resolve()
        else:
            # If it's already a Path, just resolve it
            return path.resolve()


def get_path_manager() -> PathManager:
    """
    Get the singleton instance of the PathManager.
    
    Returns:
        The PathManager instance.
    """
    return PathManager()
