"""
Remote control service for handling joystick device communication and event parsing.

This service encapsulates all low-level device I/O operations and can be used
independently from the queue-based event loop for maximum reusability.
"""

import array
from fcntl import ioctl
import os
import struct
import time
from typing import Dict, Optional, Tuple

from spotmicroai.logger import Logger
from spotmicroai import labels
from spotmicroai.constants import (
    DEADZONE,
    AXIS_UPDATE_THRESHOLD,
    RECONNECT_RETRY_DELAY,
    JSDEV_READ_SIZE,
)

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
        axis_states: Dictionary mapping axis names to their current values (0.0-1.0)
        button_states: Dictionary mapping button names to their current values (0 or 1)
    """

    def __init__(self, device_name: str):
        """
        Initialize the Remote Control Service.

        Args:
            device_name: The device name to search for (e.g., 'js0')
        """
        self.device_name = device_name
        self.jsdev: Optional[object] = None
        self.axis_states: Dict[str, float] = {}
        self.button_states: Dict[str, int] = {}
        self.button_map: list = []
        self.axis_map: list = []
        self.is_connected = False

    def check_for_connected_devices(self) -> bool:
        """
        Scan /dev/input for the configured joystick device and attempt to open it.

        Returns:
            True if device was found and opened, False otherwise.
        """
        log.info(labels.REMOTE_LOOKING_FOR_DEVICES.format(self.device_name))
        self.is_connected = False
        self.jsdev = None

        for fn in os.listdir('/dev/input'):
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
        device_path = f'/dev/input/{device_name}'

        # Attempt to open device with retries
        while True:
            try:
                log.debug(labels.REMOTE_ATTEMPTING_OPEN.format(device_path))
                self.jsdev = open(device_path, 'rb')
                os.set_blocking(self.jsdev.fileno(), False)
                log.info(labels.REMOTE_OPEN_SUCCESS.format(device_path))
                break
            except Exception as e:
                log.warning(labels.REMOTE_OPEN_WARNING.format(device_path, RECONNECT_RETRY_DELAY, e))
                time.sleep(RECONNECT_RETRY_DELAY)

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
        ioctl(self.jsdev, 0x80006A13 + (0x10000 * len(buf)), buf)  # type: ignore
        js_name = buf.tobytes().rstrip(b'\x00').decode('utf-8')
        log.info('Connected to device: %s', js_name)

        # Get number of axes and buttons
        buf = array.array('B', [0])
        ioctl(self.jsdev, 0x80016A11, buf)  # type: ignore
        num_axes = buf[0]

        buf = array.array('B', [0])
        ioctl(self.jsdev, 0x80016A12, buf)  # type: ignore
        num_buttons = buf[0]

        # Clear previous mappings
        self.axis_map.clear()
        self.button_map.clear()
        self.axis_states.clear()
        self.button_states.clear()

        # Get the axis map
        axis_names = self._get_axis_names()
        buf = array.array('B', [0] * 0x40)
        ioctl(self.jsdev, 0x80406A32, buf)  # type: ignore
        for axis in buf[:num_axes]:
            axis_name = axis_names.get(axis, f'unknown(0x{axis:02x})')
            self.axis_map.append(axis_name)
            self.axis_states[axis_name] = 0.0

        # Get the button map
        button_names = self._get_button_names()
        buf = array.array('H', [0] * 200)
        ioctl(self.jsdev, 0x80406A34, buf)  # type: ignore
        for btn in buf[:num_buttons]:
            btn_name = button_names.get(btn, f'unknown(0x{btn:03x})')
            self.button_map.append(btn_name)
            self.button_states[btn_name] = 0

        log.info(labels.REMOTE_AXES_FOUND.format(num_axes, ", ".join(self.axis_map)))
        log.info(labels.REMOTE_BUTTONS_FOUND.format(num_buttons, ", ".join(self.button_map)))

    @staticmethod
    def _get_axis_names() -> Dict[int, str]:
        """Get the standard Linux input axis mappings."""
        return {
            0x00: 'lx',
            0x01: 'ly',
            0x02: 'lz',
            0x03: 'rx',
            0x04: 'ry',
            0x05: 'rz',
            0x06: 'trottle',
            0x07: 'rudder',
            0x08: 'wheel',
            0x09: 'gas',
            0x0A: 'brake',
            0x10: 'hat0x',
            0x11: 'hat0y',
            0x12: 'hat1x',
            0x13: 'hat1y',
            0x14: 'hat2x',
            0x15: 'hat2y',
            0x16: 'hat3x',
            0x17: 'hat3y',
            0x18: 'pressure',
            0x19: 'distance',
            0x1A: 'tilt_x',
            0x1B: 'tilt_y',
            0x1C: 'tool_width',
            0x20: 'volume',
            0x28: 'misc',
        }

    @staticmethod
    def _get_button_names() -> Dict[int, str]:
        """Get the standard Linux input button mappings."""
        return {
            0x120: 'trigger',
            0x121: 'thumb',
            0x122: 'thumb2',
            0x123: 'top',
            0x124: 'top2',
            0x125: 'pinkie',
            0x126: 'base',
            0x127: 'base2',
            0x128: 'base3',
            0x129: 'base4',
            0x12A: 'base5',
            0x12B: 'base6',
            0x12F: 'dead',
            0x130: 'a',
            0x131: 'b',
            0x132: 'c',
            0x133: 'x',
            0x134: 'y',
            0x135: 'z',
            0x136: 'tl',
            0x137: 'tr',
            0x138: 'tl2',
            0x139: 'tr2',
            0x13A: 'select',
            0x13B: 'start',
            0x13C: 'mode',
            0x13D: 'thumbl',
            0x13E: 'thumbr',
            0x220: 'dpad_up',
            0x221: 'dpad_down',
            0x222: 'dpad_left',
            0x223: 'dpad_right',
            # Xbox 360 controller specific
            0x2C0: 'dpad_left',
            0x2C1: 'dpad_right',
            0x2C2: 'dpad_up',
            0x2C3: 'dpad_down',
        }

    def read_and_parse_events(self) -> Tuple[bool, Optional[Dict]]:
        """
        Read and parse a single event from the joystick device buffer.

        Processes one event per call and applies filtering (deadzone, threshold).

        Returns:
            Tuple of (event_read: bool, state_dict: Optional[Dict])
            - event_read: True if an event was read and processed, False if buffer was empty
            - state_dict: Dictionary of combined axis_states and button_states if read,
                         None if no event was read
        """
        if not self.is_connected or self.jsdev is None:
            return False, None

        try:
            evbuf = self.jsdev.read(JSDEV_READ_SIZE)  # type: ignore

            if not evbuf:
                return False, None

            _, value, event_type, number = struct.unpack('IhBB', evbuf)

            # Skip initialization events
            if event_type & 0x80:
                return False, None

            # Button event
            if event_type & 0x01:
                if number < len(self.button_map):
                    button = self.button_map[number]
                    if button:
                        self.button_states[button] = value

            # Axis event
            elif event_type & 0x02:
                if number < len(self.axis_map):
                    axis = self.axis_map[number]
                    if axis:
                        fvalue = round(value / 32767.0, 3)

                        # Apply deadzone filter
                        if abs(fvalue) < DEADZONE:
                            fvalue = 0.0

                        # Only update if significantly changed
                        if abs(fvalue - self.axis_states.get(axis, 0.0)) >= AXIS_UPDATE_THRESHOLD:
                            self.axis_states[axis] = fvalue

            # Return combined state after processing event
            combined = {**self.button_states, **self.axis_states}
            return True, combined

        except Exception as e:
            log.error(labels.REMOTE_READ_ERROR.format(e))
            self.is_connected = False
            if self.jsdev:
                self.jsdev.close()  # type: ignore
                self.jsdev = None
            return False, None

    def get_current_state(self) -> Dict:
        """
        Get the current state of all axes and buttons without reading new events.

        Returns:
            Dictionary of combined axis_states and button_states
        """
        return {**self.button_states, **self.axis_states}

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
