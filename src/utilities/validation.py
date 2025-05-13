"""
Validation utilities for the utilities package.

This module provides validation functions for paths, environment variables,
and other utility-related data.
"""

import os
import re
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union, cast

from .exceptions import PathValidationError, EnvironmentVariableValidationError

T = TypeVar('T')


def validate_path_exists(path: Union[str, Path]) -> Path:
    """
    Validate that a path exists on the filesystem.
    
    Args:
        path: The path to validate.
        
    Returns:
        The validated path as a Path object.
        
    Raises:
        PathValidationError: If the path does not exist.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise PathValidationError(f"Path does not exist: {path}")
    return path_obj


def validate_directory_exists(path: Union[str, Path]) -> Path:
    """
    Validate that a path exists and is a directory.
    
    Args:
        path: The path to validate.
        
    Returns:
        The validated path as a Path object.
        
    Raises:
        PathValidationError: If the path does not exist or is not a directory.
    """
    path_obj = validate_path_exists(path)
    if not path_obj.is_dir():
        raise PathValidationError(f"Path is not a directory: {path}")
    return path_obj


def validate_file_exists(path: Union[str, Path]) -> Path:
    """
    Validate that a path exists and is a file.
    
    Args:
        path: The path to validate.
        
    Returns:
        The validated path as a Path object.
        
    Raises:
        PathValidationError: If the path does not exist or is not a file.
    """
    path_obj = validate_path_exists(path)
    if not path_obj.is_file():
        raise PathValidationError(f"Path is not a file: {path}")
    return path_obj


def validate_path_writable(path: Union[str, Path]) -> Path:
    """
    Validate that a path is writable.
    
    Args:
        path: The path to validate.
        
    Returns:
        The validated path as a Path object.
        
    Raises:
        PathValidationError: If the path is not writable.
    """
    path_obj = Path(path)
    
    # Check if the path exists
    if path_obj.exists():
        # If it's a file, check if it's writable
        if path_obj.is_file() and not os.access(path_obj, os.W_OK):
            raise PathValidationError(f"File is not writable: {path}")
        # If it's a directory, check if it's writable
        elif path_obj.is_dir() and not os.access(path_obj, os.W_OK):
            raise PathValidationError(f"Directory is not writable: {path}")
    else:
        # If the path doesn't exist, check if the parent directory is writable
        parent = path_obj.parent
        if not parent.exists():
            raise PathValidationError(f"Parent directory does not exist: {parent}")
        if not os.access(parent, os.W_OK):
            raise PathValidationError(f"Parent directory is not writable: {parent}")
    
    return path_obj


def validate_path_readable(path: Union[str, Path]) -> Path:
    """
    Validate that a path is readable.
    
    Args:
        path: The path to validate.
        
    Returns:
        The validated path as a Path object.
        
    Raises:
        PathValidationError: If the path is not readable.
    """
    path_obj = validate_path_exists(path)
    if not os.access(path_obj, os.R_OK):
        raise PathValidationError(f"Path is not readable: {path}")
    return path_obj


def validate_path_executable(path: Union[str, Path]) -> Path:
    """
    Validate that a path is executable.
    
    Args:
        path: The path to validate.
        
    Returns:
        The validated path as a Path object.
        
    Raises:
        PathValidationError: If the path is not executable.
    """
    path_obj = validate_path_exists(path)
    if not os.access(path_obj, os.X_OK):
        raise PathValidationError(f"Path is not executable: {path}")
    return path_obj


def validate_env_var_type(value: str, type_func: Callable[[str], T], var_name: str) -> T:
    """
    Validate that an environment variable can be converted to the specified type.
    
    Args:
        value: The environment variable value to validate.
        type_func: The function to use for type conversion.
        var_name: The name of the environment variable (for error messages).
        
    Returns:
        The validated and converted value.
        
    Raises:
        EnvironmentVariableValidationError: If the value cannot be converted.
    """
    try:
        return type_func(value)
    except (ValueError, TypeError) as e:
        raise EnvironmentVariableValidationError(
            f"Environment variable '{var_name}' value '{value}' cannot be converted to {type_func.__name__}: {str(e)}"
        )


def validate_env_var_pattern(value: str, pattern: str, var_name: str) -> str:
    """
    Validate that an environment variable matches a regular expression pattern.
    
    Args:
        value: The environment variable value to validate.
        pattern: The regular expression pattern to match.
        var_name: The name of the environment variable (for error messages).
        
    Returns:
        The validated value.
        
    Raises:
        EnvironmentVariableValidationError: If the value does not match the pattern.
    """
    if not re.match(pattern, value):
        raise EnvironmentVariableValidationError(
            f"Environment variable '{var_name}' value '{value}' does not match pattern '{pattern}'"
        )
    return value


def validate_env_var_options(value: str, options: list[str], var_name: str) -> str:
    """
    Validate that an environment variable is one of a set of options.
    
    Args:
        value: The environment variable value to validate.
        options: The list of valid options.
        var_name: The name of the environment variable (for error messages).
        
    Returns:
        The validated value.
        
    Raises:
        EnvironmentVariableValidationError: If the value is not in the options.
    """
    if value not in options:
        raise EnvironmentVariableValidationError(
            f"Environment variable '{var_name}' value '{value}' is not one of {options}"
        )
    return value
