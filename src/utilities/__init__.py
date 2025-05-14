"""
ComAI Client Utilities Package.

This package provides essential infrastructure services for the ComAI Client,
focusing on centralizing cross-cutting concerns like path management,
environment configuration, and console output formatting.
"""

from .path_manager import PathManager, get_path_manager
from .environment_manager import EnvironmentManager, get_environment_manager
from .console_manager import ConsoleManager, get_console_manager, OutputFormat

__all__ = [
    'PathManager',
    'get_path_manager',
    'EnvironmentManager',
    'get_environment_manager',
    'ConsoleManager',
    'get_console_manager',
    'OutputFormat',
]
