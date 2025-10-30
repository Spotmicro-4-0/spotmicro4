#!/usr/bin/env python3
"""
ConfigApp - JSON-driven terminal UI for configuring SpotMicroAI.

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
        "title": "SpotMicroAI Config App",
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

import json
from pathlib import Path

import curses
from enum import Enum
import subprocess
import sys
from typing import Any, Mapping

import spotmicroai.labels as LABELS
from spotmicroai.ui import theme as THEME, ui_utils


class MenuAction(Enum):
    SUBMENU = "submenu"
    BACK = "back"
    EXIT = "exit"
    RUN = "run"


class ConfigApp:
    """
    Core curses-based menu handler.

    Attributes:
        menus (dict): Parsed JSON structure containing all menu definitions.
        menu_stack (list[tuple]): Stack of active menus as (menu_name, context_dict) tuples.
        context_stack (list[dict]): Stack of context dictionaries for parameter interpolation.
        current_index (int): Currently highlighted menu item index.
    """

    # UI Layout Constants
    MIN_TERMINAL_HEIGHT = 10
    MIN_TERMINAL_WIDTH = 30
    BOX_MAX_WIDTH = 70
    BOX_MARGIN_X = 10
    BOX_MARGIN_Y = 4
    INNER_MARGIN_LEFT = 4
    INNER_MARGIN_TOTAL = 8
    LAYOUT_OVERHEAD = 7
    MIN_BOX_HEIGHT = 8
    MSG_TOO_SMALL_WIDTH = 20
    MSG_RESIZE_WIDTH = 30
    MSG_HEIGHT_SMALL_WIDTH = 25
    TITLE_Y_OFFSET = 1
    SCROLL_UP_Y_OFFSET = 2
    OPTIONS_Y_OFFSET = 3
    SCROLL_DOWN_Y_OFFSET_FROM_BOTTOM = 3
    HELP_Y_OFFSET_FROM_BOTTOM = 2
    SAFETY_Y_CHECK_FROM_BOTTOM = 2
    HELP_INNER_MARGIN = 2
    TITLE_INNER_MARGIN = 1

    def __init__(self, menus: Mapping[str, Any], entry_menu: str = "main", context: dict | None = None) -> None:
        """
        Initialize the ConfigApp with in-memory menu definitions.

        Args:
            menus (Mapping[str, Any]): Menu definitions keyed by menu name.
            entry_menu (str): Entry point menu key. Defaults to "main".
            context (dict | None): Initial context for parameter interpolation. Defaults to None.
        """
        if entry_menu not in menus:
            raise KeyError(f"Entry menu '{entry_menu}' not found in menu definitions.")

        self.menus = dict(menus)
        self.menu_stack = [(entry_menu, context or {})]
        self.current_index = 0
        self.scroll_offset = 0  # Track scroll position for viewport
        self.stdscr = None  # Will be set in _main_loop

    # -------------------------------------------------------------------------
    # Main Execution Loop
    # -------------------------------------------------------------------------
    def _get_current_menu_name(self) -> str:
        """Get the current menu name from the top of the stack."""
        return self.menu_stack[-1][0]

    def _get_current_context(self) -> dict:
        """Get the current context from the top of the stack."""
        return self.menu_stack[-1][1]

    def _interpolate(self, text: str | None) -> str:
        """Interpolate context variables in text using {VARIABLE} format."""
        if not text or not isinstance(text, str):
            return ""
        context = self._get_current_context()
        try:
            return text.format(**context)
        except (KeyError, ValueError):
            # If interpolation fails, return original text
            return text

    def run(self) -> None:
        """Start the curses rendering loop."""
        try:
            curses.wrapper(self._main_loop)
        except KeyboardInterrupt:
            # Clean exit on Ctrl+C
            curses.endwin()
            sys.exit(0)

    def _main_loop(self, stdscr) -> None:
        """Render and handle input for the current active menu."""
        self.stdscr = stdscr  # Store for use in error handling
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)  # Enable number keypad

        # Initialize color pairs from the central DEFAULT_THEME
        ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)

        try:
            while True:
                self._draw_menu(stdscr)
                if not self._handle_key_input(stdscr):
                    break
        except KeyboardInterrupt:
            # Clean exit on Ctrl+C
            pass

    def _handle_key_input(self, stdscr) -> bool:
        """Handle key input for menu navigation."""
        key = stdscr.getch()
        options = self.menus[self._get_current_menu_name()].get("options", [])

        # Navigation keys
        if key in (curses.KEY_UP, ord("k")):
            self.current_index = (self.current_index - 1) % len(options)
            self._adjust_scroll_offset(stdscr)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.current_index = (self.current_index + 1) % len(options)
            self._adjust_scroll_offset(stdscr)
        elif key == curses.KEY_PPAGE:  # Page Up
            h, _ = stdscr.getmaxyx()
            page_size = max(1, self._calculate_visible_items(h) - 1)
            self.current_index = max(0, self.current_index - page_size)
            self._adjust_scroll_offset(stdscr)
        elif key == curses.KEY_NPAGE:  # Page Down
            h, _ = stdscr.getmaxyx()
            page_size = max(1, self._calculate_visible_items(h) - 1)
            self.current_index = min(len(options) - 1, self.current_index + page_size)
            self._adjust_scroll_offset(stdscr)

        # Selection
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            self._execute_option(options[self.current_index])

        # Quit and Back
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

        # Number shortcuts
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
        ui_utils.CursesUIHelper.draw_shadow(stdscr, start_y, start_x, box_width, box_height, h, w)

    def _draw_borders(self, stdscr, start_y: int, start_x: int, box_width: int, box_height: int) -> None:
        """Draw borders for the menu box safely."""
        ui_utils.CursesUIHelper.draw_borders(stdscr, start_y, start_x, box_width, box_height)

    def _draw_box_content(self, stdscr, start_y: int, start_x: int, box_width: int, box_height: int) -> None:
        """Draw inner box content safely."""
        ui_utils.CursesUIHelper.draw_box_content(stdscr, start_y, start_x, box_width, box_height)

    def _calculate_visible_items(self, terminal_height: int) -> int:
        """Calculate how many menu items can fit in the terminal."""
        # Account for: borders (2), title (2), spacing (2), help text (1), shadow (1)
        min_box_height = self.MIN_BOX_HEIGHT
        max_box_height = terminal_height - self.BOX_MARGIN_Y
        if max_box_height < min_box_height:
            return 0
        # Items that fit = box_height - (borders + title + spacing + help text)
        return max(0, max_box_height - self.LAYOUT_OVERHEAD)

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

    def _draw_terminal_too_small(self, stdscr, h: int, w: int) -> None:
        """Draw message when terminal is too small."""
        msg1 = LABELS.MSG_TERMINAL_TOO_SMALL
        msg2 = LABELS.MSG_RESIZE_CONTINUE

        # Find the longest message to determine padding width
        max_msg_width = max(len(msg1), len(msg2))

        # Center and pad both messages to equal width, then add 1 char padding on left and right
        msg1_padded = f" {msg1.center(max_msg_width)} "
        msg2_padded = f" {msg2.center(max_msg_width)} "

        try:
            stdscr.addstr(
                h // 2,
                max(0, (w - len(msg1_padded)) // 2),
                msg1_padded,
                curses.color_pair(THEME.REGULAR_ROW),
            )
            stdscr.addstr(
                h // 2 + 1,
                max(0, (w - len(msg2_padded)) // 2),
                msg2_padded,
                curses.color_pair(THEME.REGULAR_ROW),
            )
        except curses.error:
            pass
        stdscr.refresh()

    def _draw_error_box(self, stdscr, message: str) -> None:
        """Draw an error message box and wait for user to press a key."""
        ui_utils.CursesUIHelper.draw_error_box(stdscr, message, self.BOX_MAX_WIDTH)

    def _draw_help_text(self, stdscr, start_x, start_y, box_width, box_height):
        # Always draw help text at the bottom of the box
        help_text = LABELS.MSG_HELP_TEXT
        help_x = max(start_x + self.TITLE_INNER_MARGIN, start_x + (box_width - len(help_text)) // 2)
        help_y = start_y + box_height - self.HELP_Y_OFFSET_FROM_BOTTOM
        try:
            # Use dim attribute for subtle text (like italics)
            stdscr.addstr(
                help_y,
                help_x,
                help_text[: max(0, box_width - self.HELP_INNER_MARGIN)],
                curses.color_pair(THEME.REGULAR_ROW) | curses.A_DIM,
            )
        except curses.error:
            pass

    def _draw_menu(self, stdscr) -> None:
        """Draw menu safely, responsive to resize."""
        h, w = stdscr.getmaxyx()

        stdscr.bkgd(' ', curses.color_pair(THEME.BACKGROUND))
        stdscr.clear()

        # Avoid crash if terminal is too small
        if h < self.MIN_TERMINAL_HEIGHT or w < self.MIN_TERMINAL_WIDTH:
            self._draw_terminal_too_small(stdscr, h, w)
            return

        current_menu = self.menus[self._get_current_menu_name()]
        title = self._interpolate(current_menu.get("title", "Menu"))
        options = current_menu.get("options", [])

        # Calculate visible items based on terminal height
        visible_items = self._calculate_visible_items(h)

        if visible_items == 0:
            try:
                stdscr.addstr(
                    h // 2,
                    max(0, (w - self.MSG_HEIGHT_SMALL_WIDTH) // 2),
                    LABELS.MSG_HEIGHT_TOO_SMALL,
                    curses.color_pair(THEME.REGULAR_ROW),
                )
            except curses.error:
                pass
            stdscr.refresh()
            return

        box_width = min(w - self.BOX_MARGIN_X, self.BOX_MAX_WIDTH)
        # Box height accounts for visible items, not all items
        # Add 7 for: borders (2) + title (2) + spacing (2) + help text (1)
        box_height = min(visible_items + self.LAYOUT_OVERHEAD, h - self.BOX_MARGIN_Y)
        start_y = max(1, (h - box_height) // 2)
        start_x = max(1, (w - box_width) // 2)

        self._draw_shadow(stdscr, start_y, start_x, box_width, box_height, h, w)
        self._draw_borders(stdscr, start_y, start_x, box_width, box_height)
        self._draw_box_content(stdscr, start_y, start_x, box_width, box_height)

        # Title
        title_x = max(start_x + self.TITLE_INNER_MARGIN, start_x + (box_width - len(title)) // 2)
        try:
            stdscr.addstr(
                start_y + self.TITLE_Y_OFFSET,
                title_x,
                title[: max(0, w - title_x)],
                curses.color_pair(THEME.REGULAR_ROW),
            )
        except curses.error:
            pass

        # Draw scroll indicator at top if scrolled down
        if self.scroll_offset > 0:
            indicator = THEME.SCROLL_UP
            indicator_x = max(start_x + self.TITLE_INNER_MARGIN, start_x + (box_width - len(indicator)) // 2)
            try:
                stdscr.addstr(
                    start_y + self.SCROLL_UP_Y_OFFSET, indicator_x, indicator, curses.color_pair(THEME.REGULAR_ROW)
                )
            except curses.error:
                pass

        # Options - draw only visible items
        items_end = min(self.scroll_offset + visible_items, len(options))
        is_main_menu = len(self.menu_stack) == 1

        for i in range(self.scroll_offset, items_end):
            opt = options[i]
            raw_label = opt.get('label', '')
            label = self._interpolate(raw_label) if raw_label else ""
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
            y_pos = start_y + self.OPTIONS_Y_OFFSET + display_index
            x_pos = start_x + self.INNER_MARGIN_LEFT

            # Safety check - should never happen with proper calculations
            if y_pos >= start_y + box_height - self.SAFETY_Y_CHECK_FROM_BOTTOM:
                break

            try:
                if i == self.current_index:
                    stdscr.addstr(
                        y_pos,
                        x_pos,
                        ' ' * (box_width - self.INNER_MARGIN_TOTAL),
                        curses.color_pair(THEME.HIGHLIGHTED_ROW),
                    )
                    stdscr.addstr(
                        y_pos,
                        x_pos,
                        labeled_item[: max(0, box_width - self.INNER_MARGIN_TOTAL)],
                        curses.color_pair(THEME.HIGHLIGHTED_ROW),
                    )
                else:
                    stdscr.addstr(
                        y_pos,
                        x_pos,
                        labeled_item[: max(0, box_width - self.INNER_MARGIN_TOTAL)],
                        curses.color_pair(THEME.REGULAR_ROW),
                    )
            except curses.error:
                pass

        # Draw scroll indicator at bottom if there are more items
        if self.scroll_offset + visible_items < len(options):
            indicator = THEME.SCROLL_DOWN
            indicator_x = max(start_x + self.TITLE_INNER_MARGIN, start_x + (box_width - len(indicator)) // 2)
            indicator_y = start_y + box_height - self.SCROLL_DOWN_Y_OFFSET_FROM_BOTTOM  # One row above help text
            try:
                stdscr.addstr(indicator_y, indicator_x, indicator, curses.color_pair(THEME.REGULAR_ROW))
            except curses.error:
                pass

        self._draw_help_text(stdscr, start_x, start_y, box_width, box_height)

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
            self._error(LABELS.MSG_INVALID_ACTION.format(action_str))
            return

        if action == MenuAction.SUBMENU:
            target = option.get("target")
            params = option.get("params", {})
            if not isinstance(target, str):
                self._error(LABELS.MSG_INVALID_SUBMENU_TARGET)
                return
            if target not in self.menus:
                self._error(LABELS.MSG_SUBMENU_NOT_FOUND.format(target))
                return
            if not isinstance(params, dict):
                self._error("Invalid parameters for submenu")
                return
            self.menu_stack.append((target, params))
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
            command = option.get("command")
            interpolated_command = self._interpolate(command)
            self._run_command(interpolated_command)

    # -------------------------------------------------------------------------
    # Command Runner
    # -------------------------------------------------------------------------
    def _run_command(self, command: str | None) -> None:
        """Run a shell command outside curses and return to menu afterward."""
        if not command:
            self._error(LABELS.MSG_MISSING_COMMAND)
            return

        if self.stdscr:
            # Temporarily exit curses mode to run command
            curses.def_prog_mode()  # Save current curses mode
            curses.endwin()

        error_occurred = False
        error_message = None

        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            error_occurred = True
            error_message = f"Command failed with exit code {e.returncode}"
            print(LABELS.MSG_COMMAND_FAILED.format(e.returncode))
        except KeyboardInterrupt:
            error_occurred = True
            error_message = "Command interrupted by user"
            print("\n[INFO] Command interrupted by user")

        if self.stdscr:
            # Restore curses mode
            curses.reset_prog_mode()
            self.stdscr.refresh()

            # Show error in a nice box if command failed
            if error_occurred and error_message:
                self._draw_error_box(self.stdscr, error_message)

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    def _error(self, msg: str) -> None:
        """Display error message in a box within the curses interface."""
        if self.stdscr:
            # Display error in a nice box instead of exiting curses
            self._draw_error_box(self.stdscr, msg)
        else:
            # Fallback if stdscr is not available (shouldn't happen)
            curses.endwin()
            print(LABELS.MSG_ERROR_PREFIX.format(msg))
            try:
                input(f"\n{LABELS.MSG_PRESS_ENTER_CONTINUE}")
            except KeyboardInterrupt:
                print("\n")
                sys.exit(0)

    @staticmethod
    def _dummy_screen(stdscr):
        """No-op screen refresh to resume curses cleanly."""
        stdscr.clear()
        stdscr.refresh()


def load_menus(base_dir: Path) -> dict[str, dict]:
    """
    Load and merge multiple menu JSON files into a single dictionary in memory.

    Args:
        base_dir (Path): Directory containing menu files.

    Returns:
        dict: Combined menu structure.
    """
    combined: dict[str, dict] = {}

    if not base_dir.exists():
        raise FileNotFoundError(f"Menu directory not found: {base_dir}")

    json_files = sorted(base_dir.glob("*.json"))
    if not json_files:
        print(f"[WARN] No menu definitions found in {base_dir}")

    for file_path in json_files:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            combined.update(data)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse {file_path}: {e}")

    return combined


def main() -> None:
    """
    Application entry point for the Config App.

    1. Load all menu definition files dynamically.
    2. Combine them in memory.
    3. Start the ConfigApp UI with entry_menu="main".
    """
    base_dir = Path(__file__).resolve().parent / "menus"

    menus = load_menus(base_dir)
    if "main" not in menus:
        raise KeyError("Missing 'main' menu in loaded definitions.")

    app = ConfigApp(menus, entry_menu="main")
    app.run()


if __name__ == "__main__":
    main()
