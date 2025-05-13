"""
Custom exceptions for the utilities package.

This module defines custom exceptions used throughout the utilities package
to provide more specific error handling and better error messages.
"""

class UtilityError(Exception):
    """Base exception for all utility-related errors."""
    pass


class PathError(UtilityError):
    """Base exception for all path-related errors."""
    pass


class PathNotFoundError(PathError):
    """Exception raised when a requested path is not found in the registry."""
    pass


class PathValidationError(PathError):
    """Exception raised when path validation fails."""
    pass


class PathResolutionError(PathError):
    """Exception raised when path resolution fails."""
    pass


class EnvironmentError(UtilityError):
    """Base exception for all environment-related errors."""
    pass


class EnvironmentVariableNotFoundError(EnvironmentError):
    """Exception raised when a requested environment variable is not found."""
    pass


class EnvironmentVariableValidationError(EnvironmentError):
    """Exception raised when environment variable validation fails."""
    pass


class EnvironmentLoadError(EnvironmentError):
    """Exception raised when loading environment variables fails."""
    pass
