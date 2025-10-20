#!/home/pi/spotmicroai/venv/bin/python3 -u

# Released by rdb under the Unlicense (unlicense.org)
# Based on information from:
# https://www.kernel.org/doc/Documentation/input/joystick-api.txt

import array
from fcntl import ioctl
import os
import struct
import sys
import time

from spotmicroai.runtime.utilities.config import Config
from spotmicroai.runtime.utilities.log import Logger

log = Logger().setup_logger('Testing remote controller')

# Iterate over the joystick devices.
log.info('Available devices:')

for FN in os.listdir('/dev/input'):
    if FN.startswith('js'):
        log.info(f'  /dev/input/{FN}')

# We'll store the states here.
axis_states = {}
button_states = {}

# These constants were borrowed from linux/input.h
axis_names = {
    0x00: 'x',
    0x01: 'y',
    0x02: 'z',
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
    # XBox 360 controller uses these codes.
    0x2C0: 'dpad_left',
    0x2C1: 'dpad_right',
    0x2C2: 'dpad_up',
    0x2C3: 'dpad_down',
}

axis_map = []
button_map = []

# Open the joystick device.

config = Config()
connected_device = config.remote_controller.device
FN = '/dev/input/' + str(connected_device)
log.info(f'Opening {FN}...')

try:
    jsdev = open(FN, 'rb')
except FileNotFoundError:
    log.error(f'Controller device not found: {FN}')
    log.error('Make sure your controller is paired and connected before running this test.')
    log.error('Check available devices above to verify the controller is detected.')
    sys.exit(1)
except PermissionError:
    log.error(f'Permission denied accessing {FN}')
    log.error('You may need to run this script with elevated permissions.')
    sys.exit(1)

# Get the device name.
# buf = bytearray(63)
buf = array.array('B', [0] * 64)
ioctl(jsdev, 0x80006A13 + (0x10000 * len(buf)), buf)  # JSIOCGNAME(len)
js_name = buf.tobytes().rstrip(b'\x00').decode('utf-8')
log.info(f'Device name: {js_name}')

# Get number of axes and buttons.
buf = array.array('B', [0])
ioctl(jsdev, 0x80016A11, buf)  # JSIOCGAXES
num_axes = buf[0]

buf = array.array('B', [0])
ioctl(jsdev, 0x80016A12, buf)  # JSIOCGBUTTONS
num_buttons = buf[0]

# Get the axis map.
buf = array.array('B', [0] * 0x40)
ioctl(jsdev, 0x80406A32, buf)  # JSIOCGAXMAP

for axis in buf[:num_axes]:
    axis_name = axis_names.get(axis, f'unknown(0x{axis:02x})')
    axis_map.append(axis_name)
    axis_states[axis_name] = 0.0

# Get the button map.
buf = array.array('H', [0] * 200)
ioctl(jsdev, 0x80406A34, buf)  # JSIOCGBTNMAP

for btn in buf[:num_buttons]:
    btn_name = button_names.get(btn, f'unknown(0x{btn:03x})')
    button_map.append(btn_name)
    button_states[btn_name] = 0

log.info(f'{num_axes} axes found: {", ".join(axis_map)}')
log.info(f'{num_buttons} buttons found: {", ".join(button_map)}')

# Main event loop - polling at 50 Hz
log.info('Starting event loop (50 Hz polling rate)...')
while True:
    evbuf = jsdev.read(8)
    if evbuf:
        timestamp, value, event_type, number = struct.unpack('IhBB', evbuf)

        if event_type & 0x80:
            log.info("(initial)")

        if event_type & 0x01:
            button = button_map[number]
            if button:
                button_states[button] = value
                if value:
                    log.info(f"{button} pressed")
                else:
                    log.info(f"{button} released")

        if event_type & 0x02:
            axis = axis_map[number]
            if axis:
                fvalue = value / 32767.0
                axis_states[axis] = fvalue
                log.info(f"{axis}: {fvalue:.3f}")

    # Sleep to maintain 50 Hz polling rate (20ms between polls)
    time.sleep(0.02)
