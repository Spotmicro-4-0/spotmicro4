"""Theme definitions for setup_menu.

Central place for color pair ids and default color assignments.
"""

import curses
from typing import Dict, Tuple

# Named color-pair ids
REGULAR_ROW: int = 1
HIGHLIGHTED_ROW: int = 2
BACKGROUND: int = 3
SHADOW: int = 4

# Default theme: mapping of curses color pair id -> (fg_color, bg_color)
DEFAULT_THEME: Dict[int, Tuple[int, int]] = {
    REGULAR_ROW: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    HIGHLIGHTED_ROW: (curses.COLOR_WHITE, curses.COLOR_CYAN),
    BACKGROUND: (curses.COLOR_BLUE, curses.COLOR_BLUE),
    SHADOW: (curses.COLOR_BLACK, curses.COLOR_BLACK),
}

__all__ = [
    "REGULAR_ROW",
    "HIGHLIGHTED_ROW",
    "BACKGROUND",
    "SHADOW",
    "DEFAULT_THEME",
]

# Box-drawing characters for borders (exported so callers can reuse)
TL = '┌'  # top-left
TR = '┐'  # top-right
BL = '└'  # bottom-left
BR = '┘'  # bottom-right
HOR = '─'
VERT = '│'

# Scroll indicators
SCROLL_UP = '▲'
SCROLL_DOWN = '▼'

__all__.extend(["TL", "TR", "BL", "BR", "HOR", "VERT", "SCROLL_UP", "SCROLL_DOWN"])
