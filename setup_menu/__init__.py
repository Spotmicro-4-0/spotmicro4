"""
SpotMicroAI Setup Tool Package
------------------------------
Provides the modular, curses-based setup interface for SpotMicroAI.

This package can be executed directly via:
    python3 -m setup_tool
or imported for custom automation:
    from setup_tool.menu_app import MenuApp
"""

__version__ = "1.0.0"

from .menu_app import MenuApp
