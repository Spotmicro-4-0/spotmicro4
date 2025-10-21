#!/usr/bin/env python3
"""
MenuApp - Generic JSON-driven terminal menu system for SpotMicroAI setup tool.

This module implements a curses-based hierarchical menu system that:
- Loads menu definitions from JSON files.
- Supports nested submenus and command execution.
- Handles navigation via arrow keys or `j`/`k`.
- Allows quitting with `q` (always quits) or going back with `b`/`ESC`.
- Provides numerical shortcuts (1-9, 0) for quick option selection.
- Implements scrolling for menus with many items.

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
from enum import Enum
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


class MenuAction(Enum):
    SUBMENU = "submenu"
    BACK = "back"
    EXIT = "exit"
    RUN = "run"


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
        self.scroll_offset = 0  # Track scroll position for viewport

    # -------------------------------------------------------------------------
    # Main Execution Loop
    # -------------------------------------------------------------------------
    def run(self) -> None:
        """Start the curses rendering loop."""
        curses.wrapper(self._main_loop)

    def _main_loop(self, stdscr) -> None:
        """Render and handle input for the current active menu."""
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)  # Enable number keypad

        # Initialize color pairs from the central DEFAULT_THEME
        for pair_id, (fg, bg) in DEFAULT_THEME.items():
            curses.init_pair(pair_id, fg, bg)

        while True:
            self._draw_menu(stdscr)
            if not self._handle_key_input(stdscr):
                break

    def _handle_key_input(self, stdscr) -> bool:
        """Handle key input for menu navigation."""
        key = stdscr.getch()
        options = self.menus[self.menu_stack[-1]].get("options", [])

        if key in (curses.KEY_UP, ord("k")):
            self.current_index = (self.current_index - 1) % len(options)
            self._adjust_scroll_offset(stdscr)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.current_index = (self.current_index + 1) % len(options)
            self._adjust_scroll_offset(stdscr)
        elif key == curses.KEY_PPAGE:  # Page Up
            h, w = stdscr.getmaxyx()
            page_size = max(1, self._calculate_visible_items(h) - 1)
            self.current_index = max(0, self.current_index - page_size)
            self._adjust_scroll_offset(stdscr)
        elif key == curses.KEY_NPAGE:  # Page Down
            h, w = stdscr.getmaxyx()
            page_size = max(1, self._calculate_visible_items(h) - 1)
            self.current_index = min(len(options) - 1, self.current_index + page_size)
            self._adjust_scroll_offset(stdscr)
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            self._execute_option(options[self.current_index])
        elif key in (ord("q"), ord("Q")):  # q/Q always quits the entire program
            return False
        elif key == 27:  # ESC goes back one level (or quits if at main menu)
            if len(self.menu_stack) > 1:
                self.menu_stack.pop()
                self.current_index = 0
                self.scroll_offset = 0
            else:
                return False
        elif key in (ord("b"), ord("B")):  # b/B for back (goes back one level)
            if len(self.menu_stack) > 1:
                self.menu_stack.pop()
                self.current_index = 0
                self.scroll_offset = 0
        elif ord("1") <= key <= ord("9"):  # Number keys 1-9
            # Convert key to index (1 -> 0, 2 -> 1, etc.)
            target_index = key - ord("1")
            if target_index < len(options):
                self.current_index = target_index
                self._adjust_scroll_offset(stdscr)
                # Auto-execute the selected option
                self._execute_option(options[self.current_index])
        elif key == ord("0"):  # Number key 0 for 10th item
            if len(options) >= 10:
                self.current_index = 9
                self._adjust_scroll_offset(stdscr)
                # Auto-execute the selected option
                self._execute_option(options[self.current_index])
        return True

    def _draw_shadow(self, stdscr, start_y: int, start_x: int, box_width: int, box_height: int, h: int, w: int) -> None:
        """Draw shadow effect for the menu box safely."""
        for y in range(start_y + 1, min(start_y + box_height + 1, h)):
            if start_x + box_width < w:
                try:
                    stdscr.addstr(y, start_x + box_width, '  ', curses.color_pair(SHADOW))
                except curses.error:
                    pass
        if start_y + box_height < h:
            shadow_width = min(box_width, max(0, w - (start_x + 2)))
            if shadow_width > 0:
                try:
                    stdscr.addstr(start_y + box_height, start_x + 2, ' ' * shadow_width, curses.color_pair(SHADOW))
                except curses.error:
                    pass

    def _draw_borders(self, stdscr, start_y: int, start_x: int, box_width: int, box_height: int) -> None:
        """Draw borders for the menu box safely."""
        h, w = stdscr.getmaxyx()
        if start_y + box_height > h or start_x + box_width > w or start_y < 0 or start_x < 0:
            return  # skip if box doesn’t fit

        try:
            stdscr.addstr(start_y, start_x, TL + HOR * (box_width - 2) + TR, curses.color_pair(REGULAR_ROW))
            for y in range(start_y + 1, start_y + box_height - 1):
                stdscr.addstr(y, start_x, VERT, curses.color_pair(REGULAR_ROW))
                stdscr.addstr(y, start_x + box_width - 1, VERT, curses.color_pair(REGULAR_ROW))
            stdscr.addstr(
                start_y + box_height - 1, start_x, BL + HOR * (box_width - 2) + BR, curses.color_pair(REGULAR_ROW)
            )
        except curses.error:
            pass

    def _draw_box_content(self, stdscr, start_y: int, start_x: int, box_width: int, box_height: int) -> None:
        """Draw inner box content safely."""
        h, w = stdscr.getmaxyx()
        for y in range(start_y + 1, min(start_y + box_height - 1, h)):
            if start_x + 1 < w:
                try:
                    stdscr.addstr(
                        y,
                        start_x + 1,
                        ' ' * max(0, min(box_width - 2, w - start_x - 1)),
                        curses.color_pair(REGULAR_ROW),
                    )
                except curses.error:
                    pass

    def _calculate_visible_items(self, terminal_height: int) -> int:
        """Calculate how many menu items can fit in the terminal."""
        # Account for: borders (2), title (2), spacing (2), shadow (1)
        min_box_height = 7
        max_box_height = terminal_height - 4
        if max_box_height < min_box_height:
            return 0
        # Items that fit = box_height - (borders + title + spacing)
        return max(0, max_box_height - 6)

    def _adjust_scroll_offset(self, stdscr) -> None:
        """Adjust scroll offset to keep current selection visible."""
        h, _ = stdscr.getmaxyx()
        visible_items = self._calculate_visible_items(h)

        if visible_items <= 0:
            return

        # Scroll down if current index is below viewport
        if self.current_index >= self.scroll_offset + visible_items:
            self.scroll_offset = self.current_index - visible_items + 1

        # Scroll up if current index is above viewport
        if self.current_index < self.scroll_offset:
            self.scroll_offset = self.current_index

    def _draw_menu(self, stdscr) -> None:
        """Draw menu safely, responsive to resize."""
        h, w = stdscr.getmaxyx()

        stdscr.bkgd(' ', curses.color_pair(BACKGROUND))
        stdscr.clear()

        # Avoid crash if terminal is too small
        if h < 10 or w < 30:
            try:
                stdscr.addstr(h // 2, max(0, (w - 20) // 2), "Terminal too small!", curses.color_pair(REGULAR_ROW))
                stdscr.addstr(
                    h // 2 + 1, max(0, (w - 30) // 2), "Please resize to continue", curses.color_pair(REGULAR_ROW)
                )
            except curses.error:
                pass
            stdscr.refresh()
            return

        current_menu = self.menus[self.menu_stack[-1]]
        title = current_menu.get("title", "Menu")
        options = current_menu.get("options", [])

        # Calculate visible items based on terminal height
        visible_items = self._calculate_visible_items(h)

        if visible_items == 0:
            try:
                stdscr.addstr(
                    h // 2, max(0, (w - 25) // 2), "Terminal height too small", curses.color_pair(REGULAR_ROW)
                )
            except curses.error:
                pass
            stdscr.refresh()
            return

        box_width = min(w - 10, 70)
        # Box height accounts for visible items, not all items
        box_height = min(visible_items + 6, h - 4)
        start_y = max(1, (h - box_height) // 2)
        start_x = max(1, (w - box_width) // 2)

        self._draw_shadow(stdscr, start_y, start_x, box_width, box_height, h, w)
        self._draw_borders(stdscr, start_y, start_x, box_width, box_height)
        self._draw_box_content(stdscr, start_y, start_x, box_width, box_height)

        # Title
        title_x = max(start_x + 1, start_x + (box_width - len(title)) // 2)
        try:
            stdscr.addstr(start_y + 1, title_x, title[: max(0, w - title_x)], curses.color_pair(REGULAR_ROW))
        except curses.error:
            pass

        # Draw scroll indicator at top if scrolled down
        if self.scroll_offset > 0:
            indicator = "↑ More above ↑"
            indicator_x = max(start_x + 1, start_x + (box_width - len(indicator)) // 2)
            try:
                stdscr.addstr(start_y + 2, indicator_x, indicator, curses.color_pair(HIGHLIGHTED_ROW))
            except curses.error:
                pass

        # Options - draw only visible items
        items_end = min(self.scroll_offset + visible_items, len(options))
        is_main_menu = len(self.menu_stack) == 1

        for i in range(self.scroll_offset, items_end):
            opt = options[i]
            label = opt['label']
            action = opt.get('action', '')

            # Determine prefix based on position and action
            # Show Q) for exit in main menu, B) for back in submenus
            is_last_item = i == len(options) - 1

            if is_last_item and action == 'exit' and is_main_menu:
                number_prefix = "Q) "
            elif is_last_item and action == 'back' and not is_main_menu:
                number_prefix = "B) "
            elif i < 9:
                number_prefix = f"{i + 1}) "
            elif i == 9:
                number_prefix = "0) "  # 10th item uses '0' key
            else:
                number_prefix = f"{i + 1}) "  # Show number but no keyboard shortcut

            labeled_item = number_prefix + label

            # Calculate display position relative to viewport
            display_index = i - self.scroll_offset
            y_pos = start_y + 3 + display_index
            x_pos = start_x + 4

            # Safety check - should never happen with proper calculations
            if y_pos >= start_y + box_height - 2:
                break

            try:
                if i == self.current_index:
                    stdscr.addstr(y_pos, x_pos, ' ' * (box_width - 8), curses.color_pair(HIGHLIGHTED_ROW))
                    stdscr.addstr(
                        y_pos, x_pos, labeled_item[: max(0, box_width - 8)], curses.color_pair(HIGHLIGHTED_ROW)
                    )
                else:
                    stdscr.addstr(y_pos, x_pos, labeled_item[: max(0, box_width - 8)], curses.color_pair(REGULAR_ROW))
            except curses.error:
                pass

        # Draw scroll indicator at bottom if there are more items
        if self.scroll_offset + visible_items < len(options):
            indicator = "↓ More below ↓"
            indicator_x = max(start_x + 1, start_x + (box_width - len(indicator)) // 2)
            indicator_y = start_y + box_height - 2
            try:
                stdscr.addstr(indicator_y, indicator_x, indicator, curses.color_pair(HIGHLIGHTED_ROW))
            except curses.error:
                pass

        stdscr.refresh()

    # -------------------------------------------------------------------------
    # Option Execution
    # -------------------------------------------------------------------------
    def _execute_option(self, option: dict) -> None:
        """Execute an option based on its action type."""
        action_str = option.get("action")
        try:
            action = MenuAction(action_str)
        except ValueError:
            self._error(f"Invalid action: {action_str}")
            return

        if action == MenuAction.SUBMENU:
            target = option.get("target")
            if not isinstance(target, str):
                self._error("Invalid or missing submenu target.")
                return
            if target not in self.menus:
                self._error(f"Submenu '{target}' not found.")
                return
            self.menu_stack.append(target)
            self.current_index = 0
            self.scroll_offset = 0

        elif action == MenuAction.BACK:
            if len(self.menu_stack) > 1:
                self.menu_stack.pop()
                self.current_index = 0
                self.scroll_offset = 0

        elif action == MenuAction.EXIT:
            sys.exit(0)

        elif action == MenuAction.RUN:
            self._run_command(option.get("command"))

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
