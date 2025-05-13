"""
ComAI Client Utilities Package.

This package provides essential infrastructure services for the ComAI Client,
focusing on centralizing cross-cutting concerns like path management and
environment configuration.
"""

from .path_manager import PathManager, get_path_manager
from .environment_manager import EnvironmentManager, get_environment_manager

__all__ = [
    'PathManager',
    'get_path_manager',
    'EnvironmentManager',
    'get_environment_manager',
]
