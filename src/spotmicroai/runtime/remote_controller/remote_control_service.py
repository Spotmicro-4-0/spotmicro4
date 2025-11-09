"""
Remote control service for handling joystick device communication and event parsing.

This service encapsulates all low-level device I/O operations and can be used
independently from the queue-based event loop for maximum reusability.
"""

import array
from dataclasses import dataclass
from fcntl import ioctl
import os
import struct

from spotmicroai.logger import Logger
from spotmicroai import labels
from spotmicroai.constants import (
    AXIS_NORMALIZATION_CONSTANT,
    DEADZONE,
    AXIS_UPDATE_THRESHOLD,
    DEVICE_PATH,
    RECONNECT_RETRY_DELAY,
    JSDEV_READ_SIZE,
    JSIOCGNAME,
    JSIOCGAXES,
    JSIOCGBUTTONS,
    JSIOCGAXMAP,
    JSIOCGBTNMAP,
)
from spotmicroai.runtime.controller_event import ControllerEvent

from ._mappings import (
    DRIVER_CODE_TO_ROBOT_NAMES,
    JS_EVENT_AXIS,
    JS_EVENT_BUTTON,
    JS_EVENT_INIT,
)


@dataclass
class JsEvent:
    """Represents a single event from a Linux joystick device."""

    time: int  # Event timestamp (ms)
    value: int  # Value (-32767–32767 for axes, 0/1 for buttons)
    event_type: int  # Event type bitmask (JS_EVENT_AXIS, JS_EVENT_BUTTON, etc.)
    number: int  # Axis or button index


log = Logger().setup_logger('Remote Control Service')

class RemoteControlService:
    """
    Service for managing joystick device connections and parsing input events.

    This service handles:
    - Device discovery and connection
    - Axis and button mapping
    - Event buffer reading and parsing
    - State filtering (deadzone, threshold)

    Attributes:
        device_name: The configured device name to search for (e.g., 'js0')
        controller_event: ControllerEvent instance holding the current state
    """

    def __init__(self, device_name: str):
        """
        Initialize the Remote Control Service.

        Args:
            device_name: The device name to search for (e.g., 'js0')
        """
        self.device_name = device_name
        self.jsdev: object | None = None
        self._controller_event = ControllerEvent()
        self.button_codes: list = []
        self.axis_codes: list = []
        self.is_connected = False

    def _axis_normalize_and_apply_deadzone(self, value: int, axis: str) -> None:
        fvalue = round(value / AXIS_NORMALIZATION_CONSTANT, 3)

        # Apply deadzone filter
        if abs(fvalue) < DEADZONE:
            fvalue = 0.0

        # Only update if significantly changed
        current_value = getattr(self._controller_event, axis, 0.0) or 0.0
        if abs(fvalue - current_value) >= AXIS_UPDATE_THRESHOLD:
            setattr(self._controller_event, axis, fvalue)

    def scan(self) -> bool:
        """
        Scan /dev/input for the configured joystick device and attempt to open it.

        Returns:
            True if device was found and opened, False otherwise.
        """
        log.info(labels.REMOTE_LOOKING_FOR_DEVICES.format(self.device_name))
        self.is_connected = False
        self.jsdev = None

        for fn in os.listdir(DEVICE_PATH):
            if fn.startswith(str(self.device_name)):
                return self._open_device(self.device_name)

        return False

    def _open_device(self, device_name: str) -> bool:
        """
        Open a joystick device and initialize its mappings.

        Args:
            device_name: The device name to open

        Returns:
            True if device was opened and initialized, False otherwise.
        """
        device_path = f'{DEVICE_PATH}/{device_name}'

        # Attempt to open device with retries
        try:
            log.debug(labels.REMOTE_ATTEMPTING_OPEN.format(device_path))
            self.jsdev = open(device_path, 'rb')
            os.set_blocking(self.jsdev.fileno(), False)
            log.info(labels.REMOTE_OPEN_SUCCESS.format(device_path))
        except Exception as e:
            log.warning(labels.REMOTE_OPEN_WARNING.format(device_path, RECONNECT_RETRY_DELAY, e))
            return False

        # Initialize device mappings
        try:
            self._initialize_device_mappings()
            self.is_connected = True
            return True
        except Exception as e:
            log.error(labels.REMOTE_INIT_MAPPING_ERROR.format(e))
            if self.jsdev:
                self.jsdev.close()
                self.jsdev = None
            self.is_connected = False
            return False

    def _initialize_device_mappings(self) -> None:
        """
        Query the joystick device for axis and button mappings.

        Raises:
            Exception: If device operations fail
        """
        # Get the device name
        buf = array.array('B', [0] * 64)
        ioctl(self.jsdev, JSIOCGNAME + (0x10000 * len(buf)), buf)  # type: ignore
        js_name = buf.tobytes().rstrip(b'\x00').decode('utf-8')
        log.info('Connected to device: %s', js_name)

        # Get number of axes and buttons
        buf = array.array('B', [0])
        ioctl(self.jsdev, JSIOCGAXES, buf)  # type: ignore
        num_axes = buf[0]

        buf = array.array('B', [0])
        ioctl(self.jsdev, JSIOCGBUTTONS, buf)  # type: ignore
        num_buttons = buf[0]

        # Clear previous mappings
        self.axis_codes.clear()
        self.button_codes.clear()

        # Get the axis map
        buf = array.array('B', [0] * 0x40)
        ioctl(self.jsdev, JSIOCGAXMAP, buf)  # type: ignore
        for axis in buf[:num_axes]:
            self.axis_codes.append(axis)

        # Get the button map
        buf = array.array('H', [0] * 200)
        ioctl(self.jsdev, JSIOCGBTNMAP, buf)  # type: ignore
        for btn in buf[:num_buttons]:
            self.button_codes.append(btn)

        log.info(
            labels.REMOTE_AXES_FOUND.format(
                num_axes,
                ", ".join(DRIVER_CODE_TO_ROBOT_NAMES.get(axis, f'unknown(0x{axis:02x})') for axis in self.axis_codes),
            )
        )
        log.info(
            labels.REMOTE_BUTTONS_FOUND.format(
                num_buttons,
                ", ".join(DRIVER_CODE_TO_ROBOT_NAMES.get(btn, f'unknown(0x{btn:03x})') for btn in self.button_codes),
            )
        )

    def poll_events(self) -> None:
        """
        Read and parse a single event from the joystick device buffer.

        Processes one event per call and applies filtering (deadzone, threshold).
        Aggregates samples over time:
        - Buttons are OR'ed (pressed once stays pressed within the current window)
        - Axes overwrite with the latest value
        """
        if not self.is_connected or self.jsdev is None:
            return

        try:
            evbuf = self.jsdev.read(JSDEV_READ_SIZE)
            if not evbuf:
                return

            # Unpack struct into JsEvent
            event = JsEvent(*struct.unpack("IhBB", evbuf))

            # Skip initialization events
            if event.event_type & JS_EVENT_INIT:
                return

            # --- Button event ---
            if event.event_type & JS_EVENT_BUTTON:
                if event.number < len(self.button_codes):
                    driver_code = self.button_codes[event.number]
                    button = DRIVER_CODE_TO_ROBOT_NAMES.get(driver_code)
                    if button:
                        # Latest event value always overwrites previous state
                        setattr(self._controller_event, button, bool(event.value))

            # --- Axis event ---
            elif event.event_type & JS_EVENT_AXIS:
                if event.number < len(self.axis_codes):
                    driver_code = self.axis_codes[event.number]
                    axis = DRIVER_CODE_TO_ROBOT_NAMES.get(driver_code)
                    if axis:
                        # Latest axis value always replaces prior one
                        self._axis_normalize_and_apply_deadzone(event.value, axis)

        except Exception as e:
            log.error(labels.REMOTE_READ_ERROR.format(e))
            self.is_connected = False
            if self.jsdev:
                self.jsdev.close()
                self.jsdev = None

    def controller_event(self) -> ControllerEvent:
        """
        Get the current state of all axes and buttons without reading new events.

        Returns:
            Dictionary of combined axis_states and button_states
        """
        return self._controller_event

    def clear(self) -> None:
        """
        Clear the contents of the current events by resetting to neutral/unpressed state.
        """
        self._controller_event = ControllerEvent()

    def disconnect(self) -> None:
        """Close the device connection if open."""
        if self.jsdev:
            try:
                self.jsdev.close()  # type: ignore
            except Exception as e:
                log.warning(labels.REMOTE_CLOSE_WARNING.format(e))
            finally:
                self.jsdev = None
                self.is_connected = False
