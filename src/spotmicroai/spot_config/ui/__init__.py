"""
Shared UI toolkit for SpotMicroAI terminal interfaces.

Exposes theming constants and curses helpers used by the Spot configuration
utilities so other modules can import them directly from
spotmicroai.spot_config.ui.
"""

from . import theme, ui_utils

__all__ = ["theme", "ui_utils"]
