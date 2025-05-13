"""
Singleton implementation for utility classes.

This module provides a Singleton metaclass that ensures only one instance
of a class exists throughout the application lifecycle.
"""

from typing import Any, Dict, Type


class Singleton(type):
    """
    Metaclass that implements the Singleton pattern.
    
    This ensures that only one instance of a class exists and provides
    global access to that instance.
    """
    
    _instances: Dict[Type, Any] = {}
    
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """
        Override the call method to return the existing instance if it exists,
        or create a new one if it doesn't.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
            
        Returns:
            The singleton instance of the class.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
    @classmethod
    def clear_instance(cls, target_cls: Type) -> None:
        """
        Clear the instance of a specific class from the singleton registry.
        
        This is primarily used for testing purposes.
        
        Args:
            target_cls: The class whose instance should be cleared.
        """
        if target_cls in cls._instances:
            del cls._instances[target_cls]
