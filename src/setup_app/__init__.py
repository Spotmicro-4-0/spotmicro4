"""
SpotMicroAI Setup Tool Package
------------------------------
Provides the modular, curses-based setup interface for SpotMicroAI.

This package can be executed directly via:
    python3 -m setup_app
or imported for custom automation:
    from setup_app.menu_app import MenuApp
"""

__version__ = "1.0.0"

from .menu_app import MenuApp
