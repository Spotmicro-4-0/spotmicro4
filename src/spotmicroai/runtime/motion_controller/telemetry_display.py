"""
Telemetry Display Module for SpotMicroAI Motion Controller.

Provides a curses-based dashboard styled like the setup utilities so telemetry
updates render in-place without flicker. Falls back to ANSI text mode if curses
is unavailable (e.g. on Windows).
"""

from datetime import datetime
import atexit
from typing import Any, Dict, Optional

try:  # Windows builds may not ship with curses
    import curses
except ImportError:  # pragma: no cover - fallback path
    curses = None  # type: ignore[assignment]

from spotmicroai.ui import theme as THEME, ui_utils


class TelemetryDisplay:
    """
    Structured telemetry dashboard.

    Draws a centered panel with consistent styling using helpers shared with the
    calibration wizard and config application. Automatically switches to a simple
    ANSI renderer if curses cannot be initialized.
    """

    MIN_HEIGHT: int = 30
    MIN_WIDTH: int = 90
    PREFERRED_WIDTH: int = 96

    def __init__(self) -> None:
        self._stdscr: Optional["curses.window"] = None
        self._initialized = False
        self._text_mode = curses is None
        self._timestamp_format = "%Y-%m-%d %H:%M:%S"
        self._atexit_registered = False

    def initialize(self) -> None:
        """Initialize curses (or ANSI fallback) exactly once."""
        if self._initialized:
            return

        if self._text_mode or curses is None:
            self._initialize_text_mode()
            return

        try:
            self._stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            self._stdscr.keypad(True)

            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
                ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)
                self._stdscr.bkgd(" ", curses.color_pair(THEME.BACKGROUND))
            else:
                self._stdscr.bkgd(" ", 0)

            self._stdscr.clear()
            self._stdscr.refresh()

            try:
                curses.curs_set(0)
            except curses.error:
                pass
        except Exception:
            self._fallback_to_text_mode()
            return

        if not self._atexit_registered:
            atexit.register(self.shutdown)
            self._atexit_registered = True

        self._initialized = True

    def shutdown(self) -> None:
        """Tear down curses state safely."""
        if curses is None:
            return

        if self._stdscr is not None:
            try:
                curses.nocbreak()
                self._stdscr.keypad(False)
                curses.echo()
            except curses.error:
                pass
            try:
                curses.endwin()
            except curses.error:
                pass

        self._stdscr = None
        self._initialized = False

    def update(self, telemetry_data: Dict[str, Any]) -> None:
        """Render fresh telemetry values."""
        if not self._initialized:
            self.initialize()

        if self._text_mode or curses is None or self._stdscr is None:
            self._render_plain_text(telemetry_data)
            return

        try:
            self._render_curses(telemetry_data)
        except curses.error:
            self._fallback_to_text_mode()
            self._render_plain_text(telemetry_data)

    # --------------------------------------------------------------------- #
    # Rendering helpers
    # --------------------------------------------------------------------- #
    def _render_curses(self, telemetry_data: Dict[str, Any]) -> None:
        if self._stdscr is None or curses is None:
            return

        stdscr = self._stdscr
        stdscr.erase()

        height, width = stdscr.getmaxyx()
        lines = self._build_content_lines(telemetry_data)
        if not lines:
            stdscr.refresh()
            return

        max_line_length = max(len(text) for text, _ in lines)
        required_height = max(len(lines) + 4, self.MIN_HEIGHT)
        required_width = max(max_line_length + 6, self.MIN_WIDTH)

        if height < required_height or width < required_width:
            message = f"Resize terminal to at least {required_width}x{required_height} for telemetry."
            self._render_resize_message(height, width, message)
            stdscr.refresh()
            return

        panel_height = len(lines) + 4
        panel_width = min(max(self.PREFERRED_WIDTH, max_line_length + 6), width)

        start_y = max(0, (height - panel_height) // 2)
        start_x = max(0, (width - panel_width) // 2)

        ui_utils.CursesUIHelper.draw_box_frame(stdscr, start_y, start_x, panel_width, panel_height, height, width)

        content_y = start_y + 2
        content_x = start_x + 3
        max_content_width = max(0, panel_width - 6)

        for offset, (text, attrs) in enumerate(lines):
            ui_utils.CursesUIHelper.draw_text(
                stdscr,
                content_y + offset,
                content_x,
                text,
                max_width=max_content_width,
                attrs=attrs,
            )

        stdscr.refresh()

    def _render_plain_text(self, telemetry_data: Dict[str, Any]) -> None:
        """ANSI fallback for platforms without curses."""
        lines = [text for text, _ in self._build_content_lines(telemetry_data)]
        output = "\n".join(lines)
        print("\033[H", end="", flush=False)  # Move cursor to home to overwrite in-place
        print(output, flush=True)

    def _render_resize_message(self, height: int, width: int, message: str) -> None:
        if self._stdscr is None or curses is None:
            return

        y = max(0, height // 2)
        x = max(0, (width - len(message)) // 2)
        ui_utils.CursesUIHelper.draw_text(
            self._stdscr,
            y,
            x,
            message,
            color_pair=THEME.REGULAR_ROW,
            attrs=curses.A_BOLD if hasattr(curses, "A_BOLD") else 0,
        )

    # --------------------------------------------------------------------- #
    # Content assembly
    # --------------------------------------------------------------------- #
    def _build_content_lines(self, telemetry_data: Dict[str, Any]) -> list[tuple[str, int]]:
        bold_attr = curses.A_BOLD if curses is not None and hasattr(curses, "A_BOLD") else 0
        dim_attr = curses.A_DIM if curses is not None and hasattr(curses, "A_DIM") else 0

        lines: list[tuple[str, int]] = []

        timestamp = datetime.now().strftime(self._timestamp_format)
        lines.append(("SpotMicroAI Telemetry", bold_attr))
        lines.append((f"Timestamp: {timestamp}", 0))
        lines.append(("", 0))

        lines.extend(self._section_lines("System Status", self._system_status_lines(telemetry_data), bold_attr))
        lines.extend(self._section_lines("Motion Parameters", self._motion_lines(telemetry_data), bold_attr))
        lines.extend(self._section_lines("Controller Input", self._controller_lines(telemetry_data), bold_attr))
        lines.extend(self._section_lines("Leg Coordinates", self._leg_coordinate_lines(telemetry_data), bold_attr))
        lines.extend(self._section_lines("Servo Angles", self._servo_angle_lines(telemetry_data), bold_attr))

        if lines and lines[-1][0] == "":
            lines.pop()

        lines.append(("Press START to disable servos | Press CTRL+C to exit", dim_attr))
        return lines

    def _section_lines(self, title: str, body: list[str], bold_attr: int) -> list[tuple[str, int]]:
        if not body:
            return []

        section: list[tuple[str, int]] = [(title.upper(), bold_attr)]
        section.extend((line, 0) for line in body)
        section.append(("", 0))
        return section

    def _system_status_lines(self, telemetry_data: Dict[str, Any]) -> list[str]:
        return [
            (
                "  Activated: {activated:<3}  Running: {running:<3}  Frame Rate: {frame} Hz"
            ).format(
                activated=self._fmt_bool(telemetry_data.get("is_activated")),
                running=self._fmt_bool(telemetry_data.get("is_running")),
                frame=self._fmt_float(telemetry_data.get("frame_rate"), 1),
            ),
            (
                "  Loop Time: {loop} ms  Idle Time: {idle} ms"
            ).format(
                loop=self._fmt_float(telemetry_data.get("loop_time_ms"), 1),
                idle=self._fmt_float(telemetry_data.get("idle_time_ms"), 1),
            ),
        ]

    def _motion_lines(self, telemetry_data: Dict[str, Any]) -> list[str]:
        return [
            (
                "  Forward: {forward}  Rotation: {rotation}  Speed: {speed}"
            ).format(
                forward=self._fmt_float(telemetry_data.get("forward_factor"), 2, signed=True),
                rotation=self._fmt_float(telemetry_data.get("rotation_factor"), 2, signed=True),
                speed=self._fmt_float(telemetry_data.get("walking_speed"), 1),
            ),
            (
                "  Lean: {lean}  Height: {height}"
            ).format(
                lean=self._fmt_float(telemetry_data.get("lean_factor"), 1, signed=True),
                height=self._fmt_float(telemetry_data.get("height_factor"), 1),
            ),
            (
                "  Cycle Index: {idx}  Ratio: {ratio}  Elapsed: {elapsed} s"
            ).format(
                idx=self._fmt_int(telemetry_data.get("cycle_index")),
                ratio=self._fmt_float(telemetry_data.get("cycle_ratio"), 2),
                elapsed=self._fmt_float(telemetry_data.get("elapsed_time"), 1),
            ),
        ]

    def _controller_lines(self, telemetry_data: Dict[str, Any]) -> list[str]:
        events = telemetry_data.get("controller_events") or {}

        return [
            (
                "  Left Stick  X:{lx}  Y:{ly}    Right Stick X:{rx}  Y:{ry}"
            ).format(
                lx=self._fmt_float(events.get("lx"), 2, signed=True),
                ly=self._fmt_float(events.get("ly"), 2, signed=True),
                rx=self._fmt_float(events.get("rz"), 2, signed=True),
                ry=self._fmt_float(events.get("lz"), 2, signed=True),
            ),
            (
                "  D-Pad       X:{hatx}  Y:{haty}    Triggers    L:{brake}  R:{gas}"
            ).format(
                hatx=self._fmt_int(events.get("hat0x")),
                haty=self._fmt_int(events.get("hat0y")),
                brake=self._fmt_float(events.get("brake"), 2),
                gas=self._fmt_float(events.get("gas"), 2),
            ),
            (
                "  Buttons     A:{a:<3} B:{b:<3} X:{x:<3} Y:{y:<3} START:{start:<3} BACK:{back:<3}"
            ).format(
                a=self._fmt_bool(events.get("a")),
                b=self._fmt_bool(events.get("b")),
                x=self._fmt_bool(events.get("x")),
                y=self._fmt_bool(events.get("y")),
                start=self._fmt_bool(events.get("start")),
                back=self._fmt_bool(events.get("select")),
            ),
        ]

    def _leg_coordinate_lines(self, telemetry_data: Dict[str, Any]) -> list[str]:
        positions = telemetry_data.get("leg_positions") or {}
        return [
            (
                "  Front Right: {fr}    Front Left: {fl}"
            ).format(
                fr=self._fmt_coordinate(positions.get("front_right")),
                fl=self._fmt_coordinate(positions.get("front_left")),
            ),
            (
                "  Rear Right : {rr}    Rear Left : {rl}"
            ).format(
                rr=self._fmt_coordinate(positions.get("rear_right")),
                rl=self._fmt_coordinate(positions.get("rear_left")),
            ),
        ]

    def _servo_angle_lines(self, telemetry_data: Dict[str, Any]) -> list[str]:
        servo_angles = telemetry_data.get("servo_angles") or {}
        return [
            (
                "  Front Right  Shoulder: {sr}°  Leg: {lr}°  Foot: {fr}°"
            ).format(
                sr=self._fmt_float(servo_angles.get("front_shoulder_right"), 1),
                lr=self._fmt_float(servo_angles.get("front_leg_right"), 1),
                fr=self._fmt_float(servo_angles.get("front_foot_right"), 1),
            ),
            (
                "  Front Left   Shoulder: {sl}°  Leg: {ll}°  Foot: {fl}°"
            ).format(
                sl=self._fmt_float(servo_angles.get("front_shoulder_left"), 1),
                ll=self._fmt_float(servo_angles.get("front_leg_left"), 1),
                fl=self._fmt_float(servo_angles.get("front_foot_left"), 1),
            ),
            (
                "  Rear Right   Shoulder: {srr}°  Leg: {lrr}°  Foot: {frr}°"
            ).format(
                srr=self._fmt_float(servo_angles.get("rear_shoulder_right"), 1),
                lrr=self._fmt_float(servo_angles.get("rear_leg_right"), 1),
                frr=self._fmt_float(servo_angles.get("rear_foot_right"), 1),
            ),
            (
                "  Rear Left    Shoulder: {srl}°  Leg: {lrl}°  Foot: {frl}°"
            ).format(
                srl=self._fmt_float(servo_angles.get("rear_shoulder_left"), 1),
                lrl=self._fmt_float(servo_angles.get("rear_leg_left"), 1),
                frl=self._fmt_float(servo_angles.get("rear_foot_left"), 1),
            ),
        ]

    # --------------------------------------------------------------------- #
    # Formatting helpers
    # --------------------------------------------------------------------- #
    def _fmt_bool(self, value: Any) -> str:
        if value is None:
            return "N/A"
        if isinstance(value, bool):
            return "ON" if value else "OFF"
        if isinstance(value, (int, float)):
            return "ON" if value else "OFF"
        return str(value)

    def _fmt_float(self, value: Any, decimals: int = 2, signed: bool = False, default: str = "N/A") -> str:
        if value is None:
            return default
        try:
            number = float(value)
        except (TypeError, ValueError):
            return default

        sign_prefix = "+" if signed else ""
        fmt = f"{{:{sign_prefix}.{decimals}f}}"
        return fmt.format(number)

    def _fmt_int(self, value: Any, default: str = "N/A") -> str:
        if value is None:
            return default
        try:
            return f"{int(value)}"
        except (TypeError, ValueError):
            return default

    def _fmt_coordinate(self, coord: Any) -> str:
        if coord is None:
            return "X:  --.- Y:  --.- Z:  --.-"

        x = self._extract_component(coord, "x")
        y = self._extract_component(coord, "y")
        z = self._extract_component(coord, "z")

        return (
            f"X:{self._fmt_float(x, 1, signed=True, default=' --.-'):>7} "
            f"Y:{self._fmt_float(y, 1, signed=True, default=' --.-'):>7} "
            f"Z:{self._fmt_float(z, 1, signed=True, default=' --.-'):>7}"
        )

    @staticmethod
    def _extract_component(coord: Any, name: str) -> Any:
        if hasattr(coord, name):
            return getattr(coord, name)
        if isinstance(coord, dict):
            return coord.get(name)
        index_map = {"x": 0, "y": 1, "z": 2}
        try:
            idx = index_map[name]
            return coord[idx]  # type: ignore[index]
        except Exception:
            return None

    def _fallback_to_text_mode(self) -> None:
        """Switch from curses to ANSI rendering if curses fails."""
        if curses is not None:
            try:
                curses.echo()
                curses.nocbreak()
            except curses.error:
                pass
            try:
                curses.endwin()
            except curses.error:
                pass

        self._stdscr = None
        self._text_mode = True
        self._initialize_text_mode()

    def _initialize_text_mode(self) -> None:
        """Prepare ANSI text rendering."""
        print("\033[2J\033[H", end="", flush=True)  # Clear screen
        self._initialized = True
