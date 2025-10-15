from typing import Any, Dict


class DotDict:
    """
    A dictionary wrapper that allows dot notation access to nested dictionaries.
    This provides clean access like: config.motion_controller.buzzer.gpio_port
    """
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        
    def __getattr__(self, key: str) -> Any:
        try:
            value = self._data[key]
            # If the value is a dict, wrap it in DotDict for nested access
            if isinstance(value, dict):
                return DotDict(value)
            return value
        except KeyError:
            raise AttributeError(f"Config has no attribute '{key}'")
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access as well"""
        value = self._data[key]
        if isinstance(value, dict):
            return DotDict(value)
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Safe get with default value"""
        try:
            return self.__getattr__(key)
        except AttributeError:
            return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert back to regular dictionary"""
        return self._data
    
    def __repr__(self) -> str:
        return f"DotDict({self._data})"