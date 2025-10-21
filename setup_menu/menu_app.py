#!/usr/bin/env python3
"""
MenuApp - Generic JSON-driven terminal menu system for SpotMicroAI setup tool.

This module implements a curses-based hierarchical menu system that:
- Loads menu definitions from JSON files.
- Supports nested submenus and command execution.
- Handles navigation via arrow keys or `j`/`k`.
- Allows graceful quitting with ESC or `q`.

Example JSON:
{
    "main": {
        "title": "SpotMicroAI Setup Tool",
        "options": [
            { "label": "Deploy", "action": "submenu", "target": "deploy_menu" },
            { "label": "Run Calibration", "action": "run", "command": "python3 modules/calibrate.py" },
            { "label": "Quit", "action": "exit" }
        ]
    },
    "deploy_menu": {
        "title": "Deployment",
        "options": [
            { "label": "Copy Files", "action": "run", "command": "bash scripts/deploy.sh" },
            { "label": "Back", "action": "back" }
        ]
    }
}
"""

import curses
import subprocess
import sys
from typing import Mapping, Any

from .theme import (
    REGULAR_ROW,
    HIGHLIGHTED_ROW,
    BACKGROUND,
    SHADOW,
    DEFAULT_THEME,
    TL,
    TR,
    BL,
    BR,
    HOR,
    VERT,
)


class MenuApp:
    """
    Core curses-based menu handler.

    Attributes:
        menus (dict): Parsed JSON structure containing all menu definitions.
        menu_stack (list[str]): Stack of active menus to support nested navigation.
        current_index (int): Currently highlighted menu item index.
    """

    def __init__(self, menus: Mapping[str, Any], entry_menu: str = "main") -> None:
        """
        Initialize the MenuApp with in-memory menu definitions.

        Args:
            menus (Mapping[str, Any]): Menu definitions keyed by menu name.
            entry_menu (str): Entry point menu key. Defaults to "main".
        """
        if entry_menu not in menus:
            raise KeyError(f"Entry menu '{entry_menu}' not found in menu definitions.")

        self.menus = dict(menus)
        self.menu_stack = [entry_menu]
        self.current_index = 0

    # -------------------------------------------------------------------------
    # Main Execution Loop
    # -------------------------------------------------------------------------
    def run(self) -> None:
        """Start the curses rendering loop."""
        curses.wrapper(self._main_loop)

    def _main_loop(self, stdscr) -> None:
        """Render and handle input for the current active menu."""
        curses.curs_set(0)
        stdscr.keypad(True)

        # Initialize color pairs from the central DEFAULT_THEME
        for pair_id, (fg, bg) in DEFAULT_THEME.items():
            curses.init_pair(pair_id, fg, bg)

        while True:
            self._draw_menu(stdscr)

            # Handle key input
            key = stdscr.getch()

            options = self.menus[self.menu_stack[-1]].get("options", [])
            if key in (curses.KEY_UP, ord("k")):
                self.current_index = (self.current_index - 1) % len(options)
            elif key in (curses.KEY_DOWN, ord("j")):
                self.current_index = (self.current_index + 1) % len(options)
            elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
                self._execute_option(options[self.current_index])
            elif key in (ord("q"), ord("Q"), 27):
                if len(self.menu_stack) > 1:
                    self.menu_stack.pop()
                    self.current_index = 0
                else:
                    break

    def _draw_menu(self, stdscr) -> None:
        """Draw the current menu on the screen."""
        h, w = stdscr.getmaxyx()

        # Blue background
        stdscr.bkgd(' ', curses.color_pair(BACKGROUND))
        stdscr.clear()

        current_menu = self.menus[self.menu_stack[-1]]
        title = current_menu.get("title", "Menu")
        options = current_menu.get("options", [])

        # Calculate box dimensions
        box_width = min(w - 10, 70)
        box_height = min(len(options) + 6, h - 4)
        start_y = max(2, (h - box_height) // 2)
        start_x = (w - box_width) // 2

        # Draw shadow (right and bottom)
        for y in range(start_y + 1, min(start_y + box_height + 1, h)):
            if start_x + box_width + 1 < w:
                stdscr.addstr(y, start_x + box_width, '  ', curses.color_pair(SHADOW))
        if start_y + box_height < h:
            shadow_width = min(box_width, w - (start_x + 2))
            if shadow_width > 0:
                stdscr.addstr(start_y + box_height, start_x + 2, ' ' * shadow_width, curses.color_pair(SHADOW))

        # Top border
        stdscr.addstr(start_y, start_x, TL + HOR * (box_width - 2) + TR, curses.color_pair(REGULAR_ROW))
        # Side borders
        for y in range(start_y + 1, start_y + box_height - 1):
            stdscr.addstr(y, start_x, VERT, curses.color_pair(REGULAR_ROW))
            stdscr.addstr(y, start_x + box_width - 1, VERT, curses.color_pair(REGULAR_ROW))
        # Bottom border
        stdscr.addstr(
            start_y + box_height - 1, start_x, BL + HOR * (box_width - 2) + BR, curses.color_pair(REGULAR_ROW)
        )

        # Draw white box content
        for y in range(start_y + 1, start_y + box_height - 1):
            stdscr.addstr(y, start_x + 1, ' ' * (box_width - 2), curses.color_pair(REGULAR_ROW))

        # Draw title
        title_x = start_x + (box_width - len(title)) // 2
        stdscr.addstr(start_y + 1, title_x, title, curses.color_pair(REGULAR_ROW))

        # Draw options
        for i, opt in enumerate(options):
            label = opt['label']
            y_pos = start_y + 3 + i
            x_pos = start_x + 4

            if i == self.current_index:
                stdscr.addstr(y_pos, x_pos, ' ' * (box_width - 8), curses.color_pair(HIGHLIGHTED_ROW))
                stdscr.addstr(y_pos, x_pos, label, curses.color_pair(HIGHLIGHTED_ROW))
            else:
                stdscr.addstr(y_pos, x_pos, label, curses.color_pair(REGULAR_ROW))

        stdscr.refresh()

    # -------------------------------------------------------------------------
    # Option Execution
    # -------------------------------------------------------------------------
    def _execute_option(self, option: dict) -> None:
        """Execute an option based on its action type."""
        action = option.get("action")

        if action == "submenu":
            target = option.get("target")
            if not isinstance(target, str):
                self._error("Invalid or missing submenu target.")
                return
            if target not in self.menus:
                self._error(f"Submenu '{target}' not found.")
                return
            self.menu_stack.append(target)
            self.current_index = 0

        elif action == "back":
            if len(self.menu_stack) > 1:
                self.menu_stack.pop()
                self.current_index = 0

        elif action == "exit":
            sys.exit(0)

    # -------------------------------------------------------------------------
    # Command Runner
    # -------------------------------------------------------------------------
    def _run_command(self, command: str | None) -> None:
        """Run a shell command outside curses and return to menu afterward."""
        if not command:
            self._error("Missing 'command' field for action 'run'")
            return

        curses.endwin()
        print(f"\n[INFO] Running: {command}\n")
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Command failed with exit code {e.returncode}")
        input("\nPress Enter to return to menu...")
        curses.wrapper(self._main_loop)
        sys.exit(0)

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    @staticmethod
    def _error(msg: str) -> None:
        """Display error message."""
        curses.endwin()
        print(f"[ERROR] {msg}")
        input("\nPress Enter to continue...")
        curses.wrapper(MenuApp._dummy_screen)

    @staticmethod
    def _dummy_screen(stdscr):
        """No-op screen refresh to resume curses cleanly."""
        stdscr.clear()
        stdscr.refresh()
