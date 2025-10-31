"""
Shared UI utilities for curses-based menu and calibration interfaces.

This module provides reusable drawing functions, layout helpers, and constants
for building consistent terminal UIs across SpotMicroAI tools.
"""

import curses
from typing import Tuple

from . import theme as THEME


class CursesUIHelper:
    """Helper class for common curses UI operations."""

    @staticmethod
    def draw_shadow(stdscr, start_y: int, start_x: int, box_width: int, box_height: int, h: int, w: int) -> None:
        """Draw shadow effect for a box safely."""
        for y in range(start_y + 1, min(start_y + box_height + 1, h)):
            if start_x + box_width < w:
                try:
                    stdscr.addstr(y, start_x + box_width, "  ", curses.color_pair(THEME.SHADOW))
                except curses.error:
                    pass
        if start_y + box_height < h:
            shadow_width = min(box_width, max(0, w - (start_x + 2)))
            if shadow_width > 0:
                try:
                    stdscr.addstr(
                        start_y + box_height,
                        start_x + 2,
                        " " * shadow_width,
                        curses.color_pair(THEME.SHADOW),
                    )
                except curses.error:
                    pass

    @staticmethod
    def draw_borders(stdscr, start_y: int, start_x: int, box_width: int, box_height: int) -> None:
        """Draw borders for a box safely."""
        h, w = stdscr.getmaxyx()
        if start_y + box_height > h or start_x + box_width > w or start_y < 0 or start_x < 0:
            return  # skip if box doesn't fit

        try:
            stdscr.addstr(
                start_y,
                start_x,
                THEME.TL + THEME.HOR * (box_width - 2) + THEME.TR,
                curses.color_pair(THEME.REGULAR_ROW),
            )
            for y in range(start_y + 1, start_y + box_height - 1):
                stdscr.addstr(y, start_x, THEME.VERT, curses.color_pair(THEME.REGULAR_ROW))
                stdscr.addstr(y, start_x + box_width - 1, THEME.VERT, curses.color_pair(THEME.REGULAR_ROW))
            stdscr.addstr(
                start_y + box_height - 1,
                start_x,
                THEME.BL + THEME.HOR * (box_width - 2) + THEME.BR,
                curses.color_pair(THEME.REGULAR_ROW),
            )
        except curses.error:
            pass

    @staticmethod
    def draw_box_content(stdscr, start_y: int, start_x: int, box_width: int, box_height: int) -> None:
        """Fill the interior of a box with background color safely."""
        h, w = stdscr.getmaxyx()
        for y in range(start_y + 1, min(start_y + box_height - 1, h)):
            if start_x + 1 < w:
                try:
                    stdscr.addstr(
                        y,
                        start_x + 1,
                        " " * max(0, min(box_width - 2, w - start_x - 1)),
                        curses.color_pair(THEME.REGULAR_ROW),
                    )
                except curses.error:
                    pass

    @staticmethod
    def draw_error_box(stdscr, message: str, box_max_width: int = 70) -> None:
        """Draw an error message box and wait for user to press a key."""
        h, w = stdscr.getmaxyx()

        # Split message into lines if it's too long
        max_line_width = min(box_max_width - 8, w - 20)
        words = message.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_line_width:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Calculate box dimensions
        box_width = min(max(len(line) for line in lines) + 8, box_max_width)
        box_height = len(lines) + 6  # lines + title + spacing + prompt
        start_y = max(1, (h - box_height) // 2)
        start_x = max(1, (w - box_width) // 2)

        # Draw box components
        CursesUIHelper.draw_shadow(stdscr, start_y, start_x, box_width, box_height, h, w)
        CursesUIHelper.draw_borders(stdscr, start_y, start_x, box_width, box_height)
        CursesUIHelper.draw_box_content(stdscr, start_y, start_x, box_width, box_height)

        # Draw title
        title = "ERROR"
        title_x = start_x + (box_width - len(title)) // 2
        try:
            stdscr.addstr(
                start_y + 1,
                title_x,
                title,
                curses.color_pair(THEME.REGULAR_ROW) | curses.A_BOLD,
            )
        except curses.error:
            pass

        # Draw message lines
        for i, line in enumerate(lines):
            line_x = start_x + 4
            try:
                stdscr.addstr(
                    start_y + 3 + i,
                    line_x,
                    line[: box_width - 8],
                    curses.color_pair(THEME.REGULAR_ROW),
                )
            except curses.error:
                pass

        # Draw prompt
        prompt = "Press any key to continue..."
        prompt_x = start_x + (box_width - len(prompt)) // 2
        try:
            stdscr.addstr(
                start_y + box_height - 2,
                prompt_x,
                prompt,
                curses.color_pair(THEME.REGULAR_ROW) | curses.A_DIM,
            )
        except curses.error:
            pass

        stdscr.refresh()

        # Wait for key press
        stdscr.getch()

    @staticmethod
    def draw_text(
        stdscr,
        y: int,
        x: int,
        text: str,
        max_width: int | None = None,
        color_pair: int = THEME.REGULAR_ROW,
        attrs: int = 0,
    ) -> None:
        """Draw text safely with optional truncation and attributes."""
        try:
            h, w = stdscr.getmaxyx()
            if y < 0 or y >= h or x < 0 or x >= w:
                return

            width_to_use: int = max_width if max_width is not None else (w - x)
            width_to_use = max(0, width_to_use)
            display_text = text[:width_to_use]
            stdscr.addstr(y, x, display_text, curses.color_pair(color_pair) | attrs)
        except curses.error:
            pass

    @staticmethod
    def draw_highlighted_text(stdscr, y: int, x: int, text: str, max_width: int | None = None, attrs: int = 0) -> None:
        """Draw highlighted (selected) text safely."""
        try:
            h, w = stdscr.getmaxyx()
            if y < 0 or y >= h or x < 0 or x >= w:
                return

            width_to_use: int = max_width if max_width is not None else (w - x)
            width_to_use = max(0, width_to_use)

            # Fill background first
            stdscr.addstr(y, x, " " * width_to_use, curses.color_pair(THEME.HIGHLIGHTED_ROW))
            # Draw text on top
            display_text = text[:width_to_use]
            stdscr.addstr(y, x, display_text, curses.color_pair(THEME.HIGHLIGHTED_ROW) | attrs)
        except curses.error:
            pass

    @staticmethod
    def draw_box_frame(stdscr, start_y: int, start_x: int, box_width: int, box_height: int, h: int, w: int) -> None:
        """Draw a complete box (shadow, borders, content) in one call."""
        CursesUIHelper.draw_shadow(stdscr, start_y, start_x, box_width, box_height, h, w)
        CursesUIHelper.draw_borders(stdscr, start_y, start_x, box_width, box_height)
        CursesUIHelper.draw_box_content(stdscr, start_y, start_x, box_width, box_height)

    @staticmethod
    def clear_line(stdscr, y: int) -> None:
        """Clear a line safely."""
        try:
            stdscr.move(y, 0)
            stdscr.clrtoeol()
        except curses.error:
            pass

    @staticmethod
    def init_colors(color_theme: dict | None = None) -> None:
        """Initialize color pairs from a theme dictionary or use DEFAULT_THEME."""
        if color_theme is None:
            color_theme = THEME.DEFAULT_THEME

        for pair_id, (fg, bg) in color_theme.items():
            try:
                curses.init_pair(pair_id, fg, bg)
            except curses.error:
                pass  # Ignore if pair already initialized

    @staticmethod
    def validate_terminal_size(h: int, w: int, min_height: int = 10, min_width: int = 30) -> Tuple[bool, str]:
        """
        Validate terminal size.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if h < min_height or w < min_width:
            return False, f"Terminal too small! Requires at least {min_height}x{min_width}, got {h}x{w}"
        return True, ""
