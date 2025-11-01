"""
Reusable Singleton metaclass.
"""

from typing import Any, Dict


class Singleton(type):
    """
    Metaclass that enforces single-instance creation for subclasses.
    """

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


__all__ = [
    'Singleton',
]
