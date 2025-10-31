"""
Shared UI toolkit for SpotMicroAI terminal interfaces.

Exposes theming constants and curses helpers that were previously nested
under the spot_config package so other modules can import them directly from
spotmicroai.ui.
"""

from . import theme, ui_utils

__all__ = ["theme", "ui_utils"]
