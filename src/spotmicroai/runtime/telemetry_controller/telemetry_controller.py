"""
Telemetry controller responsible for rendering runtime metrics.
"""

import atexit
import curses
from datetime import datetime
import queue
import signal
import sys
import time
from typing import Any

from spotmicroai import labels
from spotmicroai.logger import Logger
from spotmicroai.runtime.messaging import MessageBus
from spotmicroai.runtime.motion_controller.models.telemetry_data import TelemetryData
from spotmicroai.singleton import Singleton
from spotmicroai.spot_config.ui import ui_utils, theme as THEME

log = Logger().setup_logger('Telemetry controller')


class TelemetryController(metaclass=Singleton):
    """
    Background process that ingests telemetry events and renders them.
    """

    _render_interval = 0.2  # seconds

    def __init__(self, message_bus: MessageBus) -> None:
        try:
            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            self._telemetry_topic = message_bus.telemetry
            self._display = TelemetryDisplay()
            self._display.initialize()

            self._latest_payload: TelemetryData | None = None
            self._last_render_ts = 0.0
            self._is_alive = True

            log.info(labels.TELEMETRY_INITIALIZED)
        except Exception as exc:
            self._is_alive = False
            log.error(labels.TELEMETRY_INIT_ERROR.format(exc))

    def exit_gracefully(self, _signum: int, _frame: Any) -> None:
        try:
            if hasattr(self, '_display'):
                self._display.shutdown()
        finally:
            log.info(labels.TELEMETRY_TERMINATED)
            sys.exit(0)

    def do_process_events_from_queues(self) -> None:
        if not getattr(self, '_is_alive', False):
            log.error(labels.TELEMETRY_NOT_ALIVE)
            return

        while True:
            try:
                payload = self._telemetry_topic.get(timeout=self._render_interval)
                if isinstance(payload, TelemetryData):
                    self._latest_payload = payload
                else:
                    log.debug(labels.TELEMETRY_UNEXPECTED_TYPE.format(type(payload)))
                    continue
            except queue.Empty:
                pass
            except Exception as exc:
                log.warning(labels.TELEMETRY_QUEUE_ERROR.format(exc))
                time.sleep(self._render_interval)
                continue

            if self._latest_payload is None:
                continue

            now = time.time()
            if now - self._last_render_ts < self._render_interval:
                continue

            try:
                self._display.update(self._latest_payload)
                self._last_render_ts = now
            except Exception as exc:
                log.warning(labels.TELEMETRY_RENDER_ERROR.format(exc))
                time.sleep(self._render_interval)


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
        self._stdscr: Any | None = None
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
            stdscr = self._stdscr
            if stdscr is None:
                self._fallback_to_text_mode()
                return

            stdscr.keypad(True)

            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
                ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)
                stdscr.bkgd(" ", curses.color_pair(THEME.BACKGROUND))
            else:
                stdscr.bkgd(" ", 0)

            stdscr.clear()
            stdscr.refresh()

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

        stdscr = self._stdscr
        if stdscr is not None:
            try:
                curses.nocbreak()
                stdscr.keypad(False)
                curses.echo()
            except curses.error:
                pass
            try:
                curses.endwin()
            except curses.error:
                pass

        self._stdscr = None
        self._initialized = False

    def update(self, telemetry_data: TelemetryData) -> None:
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
    def _render_curses(self, telemetry_data: TelemetryData) -> None:
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

    def _render_plain_text(self, telemetry_data: TelemetryData) -> None:
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
        stdscr = self._stdscr
        if stdscr is None:
            return
        ui_utils.CursesUIHelper.draw_text(
            stdscr,
            y,
            x,
            message,
            color_pair=THEME.REGULAR_ROW,
            attrs=curses.A_BOLD if hasattr(curses, "A_BOLD") else 0,
        )

    # --------------------------------------------------------------------- #
    # Content assembly
    # --------------------------------------------------------------------- #
    def _build_content_lines(self, telemetry_data: TelemetryData) -> list[tuple[str, int]]:
        bold_attr = curses.A_BOLD if curses is not None and hasattr(curses, "A_BOLD") else 0
        dim_attr = curses.A_DIM if curses is not None and hasattr(curses, "A_DIM") else 0

        lines: list[tuple[str, int]] = []

        timestamp = datetime.now().strftime(self._timestamp_format)
        lines.append(("SpotMicroAI Telemetry", bold_attr))
        lines.append((f"Timestamp: {timestamp}", 0))
        lines.append(("", 0))
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

    def _system_status_lines(self, telemetry_data: TelemetryData) -> list[str]:
        activated = self._fmt_bool(telemetry_data.is_activated)
        running = self._fmt_bool(telemetry_data.is_running)
        frame = self._fmt_float(telemetry_data.frame_rate, 1)
        loop = self._fmt_float(telemetry_data.loop_time_ms, 1)
        idle = self._fmt_float(telemetry_data.idle_time_ms, 1)

        return [
            f"  Activated: {activated:<3}  Running: {running:<3}  Frame Rate: {frame} Hz",
            f"  Loop Time: {loop} ms  Idle Time: {idle} ms",
        ]

    def _motion_lines(self, telemetry_data: TelemetryData) -> list[str]:
        forward = self._fmt_float(telemetry_data.forward_factor, 2, signed=True)
        rotation = self._fmt_float(telemetry_data.rotation_factor, 2, signed=True)
        speed = self._fmt_float(telemetry_data.walking_speed, 1)
        lean = self._fmt_float(telemetry_data.lean_factor, 1, signed=True)
        height = self._fmt_float(telemetry_data.height_factor, 1)
        idx = self._fmt_int(telemetry_data.cycle_index)
        ratio = self._fmt_float(telemetry_data.cycle_ratio, 2)
        elapsed = self._fmt_float(telemetry_data.elapsed_time, 1)

        return [
            f"  Forward: {forward}  Rotation: {rotation}  Speed: {speed}",
            f"  Lean: {lean}  Height: {height}",
            f"  Cycle Index: {idx}  Ratio: {ratio}  Elapsed: {elapsed} s",
        ]

    def _controller_lines(self, telemetry_data: TelemetryData) -> list[str]:
        event = telemetry_data.controller_event

        lx = self._fmt_float(event.left_stick_x if event else None, 2, signed=True)
        ly = self._fmt_float(event.left_stick_y if event else None, 2, signed=True)
        rx = self._fmt_float(event.right_stick_x if event else None, 2, signed=True)
        ry = self._fmt_float(event.right_stick_y if event else None, 2, signed=True)
        hatx = self._fmt_int(event.dpad_horizontal if event else None)
        haty = self._fmt_int(event.dpad_vertical if event else None)
        brake = self._fmt_float(event.left_trigger if event else None, 2)
        gas = self._fmt_float(event.right_trigger if event else None, 2)
        a_btn = self._fmt_bool(event.a if event else None)
        b_btn = self._fmt_bool(event.b if event else None)
        x_btn = self._fmt_bool(event.x if event else None)
        y_btn = self._fmt_bool(event.y if event else None)
        start = self._fmt_bool(event.start if event else None)
        back = self._fmt_bool(event.back if event else None)

        return [
            f"  Left Stick  X:{lx}  Y:{ly}    Right Stick X:{rx}  Y:{ry}",
            f"  D-Pad       X:{hatx}  Y:{haty}    Triggers    L:{brake}  R:{gas}",
            f"  Buttons     A:{a_btn:<3} B:{b_btn:<3} X:{x_btn:<3} Y:{y_btn:<3} START:{start:<3} BACK:{back:<3}",
        ]

    def _leg_coordinate_lines(self, telemetry_data: TelemetryData) -> list[str]:
        positions = telemetry_data.leg_positions
        front_right = self._fmt_coordinate(positions.front_right if positions else None)
        front_left = self._fmt_coordinate(positions.front_left if positions else None)
        rear_right = self._fmt_coordinate(positions.rear_right if positions else None)
        rear_left = self._fmt_coordinate(positions.rear_left if positions else None)

        return [
            f"  Front Right: {front_right}    Front Left: {front_left}",
            f"  Rear Right : {rear_right}    Rear Left : {rear_left}",
        ]

    def _servo_angle_lines(self, telemetry_data: TelemetryData) -> list[str]:
        servo_angles = telemetry_data.servo_angles
        sr = self._fmt_float(servo_angles.front_shoulder_right if servo_angles else None, 1)
        lr = self._fmt_float(servo_angles.front_leg_right if servo_angles else None, 1)
        fr = self._fmt_float(servo_angles.front_foot_right if servo_angles else None, 1)
        sl = self._fmt_float(servo_angles.front_shoulder_left if servo_angles else None, 1)
        ll = self._fmt_float(servo_angles.front_leg_left if servo_angles else None, 1)
        fl = self._fmt_float(servo_angles.front_foot_left if servo_angles else None, 1)
        srr = self._fmt_float(servo_angles.rear_shoulder_right if servo_angles else None, 1)
        lrr = self._fmt_float(servo_angles.rear_leg_right if servo_angles else None, 1)
        frr = self._fmt_float(servo_angles.rear_foot_right if servo_angles else None, 1)
        srl = self._fmt_float(servo_angles.rear_shoulder_left if servo_angles else None, 1)
        lrl = self._fmt_float(servo_angles.rear_leg_left if servo_angles else None, 1)
        frl = self._fmt_float(servo_angles.rear_foot_left if servo_angles else None, 1)

        return [
            f"  Front Right  Shoulder: {sr}°  Leg: {lr}°  Foot: {fr}°",
            f"  Front Left   Shoulder: {sl}°  Leg: {ll}°  Foot: {fl}°",
            f"  Rear Right   Shoulder: {srr}°  Leg: {lrr}°  Foot: {frr}°",
            f"  Rear Left    Shoulder: {srl}°  Leg: {lrl}°  Foot: {frl}°",
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
