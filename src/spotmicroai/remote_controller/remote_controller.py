import array
import os
import signal
import struct
import sys
import time
from fcntl import ioctl

import spotmicroai.utilities.queues as queues

# Import tunable constants
from spotmicroai.remote_controller.constants import (
    AXIS_UPDATE_THRESHOLD,
    DEADZONE,
    DEVICE_SEARCH_INTERVAL,
    PUBLISH_RATE_HZ,
    READ_LOOP_SLEEP,
    RECONNECT_RETRY_DELAY,
)
from spotmicroai.utilities.config import Config
from spotmicroai.utilities.log import Logger

log = Logger().setup_logger('Remote controller')


class RemoteControllerController:

    def __init__(self, communication_queues):
        try:
            log.debug('Starting controller...')

            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            # We'll store the states here.
            self.connected_device = False
            self.axis_states = {}
            self.button_states = {}
            self.button_map = []
            self.axis_map = []
            self.jsdev = None

            self._abort_queue = communication_queues[queues.ABORT_CONTROLLER]
            self._motion_queue = communication_queues[queues.MOTION_CONTROLLER]
            self._lcd_screen_queue = communication_queues[queues.LCD_SCREEN_CONTROLLER]

        except Exception as e:
            self._lcd_screen_queue.put(queues.LCD_SCREEN_SHOW_REMOTE_CONTROLLER_CONTROLLER_NOK)
            log.error('Remote controller controller initialization problem', e)
            sys.exit(1)

    def exit_gracefully(self, signum, frame):
        log.info('Terminated')
        sys.exit(0)

    def do_process_events_from_queues(self):
        """
        Main event loop. Reads joystick deltas but keeps publishing
        the last known state at a steady rate so that movement persists
        while the stick is held in position.
        """
        remote_controller_connected_already = False

        while True:
            if self.connected_device and not remote_controller_connected_already:
                self._lcd_screen_queue.put(queues.LCD_SCREEN_CONTROLLER_ACTION_ON)
                self._lcd_screen_queue.put(queues.LCD_SCREEN_SHOW_REMOTE_CONTROLLER_CONTROLLER_OK)
                remote_controller_connected_already = True
            else:
                time.sleep(DEVICE_SEARCH_INTERVAL)
                self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
                self._lcd_screen_queue.put(queues.LCD_SCREEN_SHOW_REMOTE_CONTROLLER_CONTROLLER_SEARCHING)
                remote_controller_connected_already = False
                self.check_for_connected_devices()
                continue

            last_publish_time = 0

            # Main event loop
            while True:
                try:
                    evbuf = self.jsdev.read(8)  # type: ignore

                    if evbuf:
                        buftime, value, type, number = struct.unpack('IhBB', evbuf)

                        # Skip initialization events
                        if type & 0x80:
                            continue

                        # Button event
                        if type & 0x01:
                            button = self.button_map[number]
                            if button:
                                self.button_states[button] = value

                        # Axis event
                        elif type & 0x02:
                            axis = self.axis_map[number]
                            if axis:
                                fvalue = round(value / 32767.0, 3)

                                # Apply deadzone filter
                                if abs(fvalue) < DEADZONE:
                                    fvalue = 0.0

                                # Only update if significantly changed
                                if abs(fvalue - self.axis_states.get(axis, 0.0)) >= AXIS_UPDATE_THRESHOLD:
                                    self.axis_states[axis] = fvalue

                    now = time.time()
                    if now - last_publish_time >= 1.0 / PUBLISH_RATE_HZ:
                        combined = {**self.button_states, **self.axis_states}
                        self._motion_queue.put(combined)
                        last_publish_time = now

                    time.sleep(READ_LOOP_SLEEP)

                except Exception as e:
                    log.error('Unknown problem while processing the queue of the remote controller', e)
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
                    remote_controller_connected_already = False
                    self.check_for_connected_devices()
                    break

    def check_for_connected_devices(self):
        """
        Scans /dev/input for the configured joystick device and opens it.
        """
        connected_device = Config().get(Config.REMOTE_CONTROLLER_CONTROLLER_DEVICE)

        log.info('The remote controller is not detected, looking for connected devices')
        self.connected_device = False
        for fn in os.listdir('/dev/input'):
            if fn.startswith(str(connected_device)):
                self.connected_device = True

                # These constants were borrowed from linux/input.h
                axis_names = {
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

                button_names = {
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

                # Open the joystick device
                fn = '/dev/input/' + str(connected_device)

                while True:
                    try:
                        log.debug(f'Attempting to open {fn}...')
                        self.jsdev = open(fn, 'rb')
                        os.set_blocking(self.jsdev.fileno(), False)
                        log.info(f'{fn} opened successfully.')
                        break
                    except Exception:
                        log.warning(f'Unable to access {fn} yet. Will retry in {RECONNECT_RETRY_DELAY} seconds...')
                        time.sleep(RECONNECT_RETRY_DELAY)

                # Get the device name
                buf = array.array('B', [0] * 64)
                ioctl(self.jsdev, 0x80006A13 + (0x10000 * len(buf)), buf)
                js_name = buf.tobytes().rstrip(b'\x00').decode('utf-8')
                log.info(f'Connected to device: {js_name}')

                # Get number of axes and buttons
                buf = array.array('B', [0])
                ioctl(self.jsdev, 0x80016A11, buf)
                num_axes = buf[0]

                buf = array.array('B', [0])
                ioctl(self.jsdev, 0x80016A12, buf)
                num_buttons = buf[0]

                # Get the axis map
                buf = array.array('B', [0] * 0x40)
                ioctl(self.jsdev, 0x80406A32, buf)
                for axis in buf[:num_axes]:
                    axis_name = axis_names.get(axis, f'unknown(0x{axis:02x})')
                    self.axis_map.append(axis_name)
                    self.axis_states[axis_name] = 0.0

                # Get the button map
                buf = array.array('H', [0] * 200)
                ioctl(self.jsdev, 0x80406A34, buf)
                for btn in buf[:num_buttons]:
                    btn_name = button_names.get(btn, f'unknown(0x{btn:03x})')
                    self.button_map.append(btn_name)
                    self.button_states[btn_name] = 0

                log.info(f'{num_axes} axes found: {", ".join(self.axis_map)}')
                log.info('%d buttons found: %s', num_buttons, ", ".join(self.button_map))

                break
