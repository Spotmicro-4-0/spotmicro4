##########################################################
# Linux Joystick / Gamepad Constants
#
# Source: Linux joystick API (see: linux/joystick.h)
# Provides symbolic constants for axis & button codes,
# plus event type bitmasks used in joystick input parsing.
##########################################################

# ────────────────────────────────────────────────
# Event Type Bitmask Flags
# ────────────────────────────────────────────────
JS_EVENT_BUTTON = 0x01   # Button pressed/released
JS_EVENT_AXIS   = 0x02   # Axis motion
JS_EVENT_INIT   = 0x80   # Initial state of device (synthetic event)

# ────────────────────────────────────────────────
# Axis Codes (Analog Inputs)
# ────────────────────────────────────────────────
AXIS_LX         = 0x00   # Left stick X
AXIS_LY         = 0x01   # Left stick Y
AXIS_LZ         = 0x02   # Right stick Y (or extra axis)
AXIS_RX         = 0x03   # Right stick X
AXIS_RY         = 0x04   # Additional axis (varies by device)
AXIS_RZ         = 0x05   # Alternate right stick axis
AXIS_THROTTLE   = 0x06   # Flight stick throttle
AXIS_RUDDER     = 0x07   # Rudder / twist
AXIS_WHEEL      = 0x08   # Steering wheel
AXIS_GAS        = 0x09   # Right trigger (gas)
AXIS_BRAKE      = 0x0A   # Left trigger (brake)
AXIS_HAT0X      = 0x10   # D-pad horizontal (-1=left, +1=right)
AXIS_HAT0Y      = 0x11   # D-pad vertical (-1=up, +1=down)
AXIS_HAT1X      = 0x12
AXIS_HAT1Y      = 0x13
AXIS_HAT2X      = 0x14
AXIS_HAT2Y      = 0x15
AXIS_HAT3X      = 0x16
AXIS_HAT3Y      = 0x17
AXIS_PRESSURE   = 0x18
AXIS_DISTANCE   = 0x19
AXIS_TILT_X     = 0x1A
AXIS_TILT_Y     = 0x1B
AXIS_TOOL_WIDTH = 0x1C
AXIS_VOLUME     = 0x20
AXIS_MISC       = 0x28

# ────────────────────────────────────────────────
# Button Codes (Digital Inputs)
# ────────────────────────────────────────────────
BTN_TRIGGER     = 0x120
BTN_THUMB       = 0x121
BTN_THUMB2      = 0x122
BTN_TOP         = 0x123
BTN_TOP2        = 0x124
BTN_PINKIE      = 0x125
BTN_BASE        = 0x126
BTN_BASE2       = 0x127
BTN_BASE3       = 0x128
BTN_BASE4       = 0x129
BTN_BASE5       = 0x12A
BTN_BASE6       = 0x12B
BTN_DEAD        = 0x12F

BTN_A           = 0x130
BTN_B           = 0x131
BTN_C           = 0x132
BTN_X           = 0x133
BTN_Y           = 0x134
BTN_Z           = 0x135
BTN_TL          = 0x136
BTN_TR          = 0x137
BTN_TL2         = 0x138
BTN_TR2         = 0x139
BTN_SELECT      = 0x13A
BTN_START       = 0x13B
BTN_MODE        = 0x13C
BTN_THUMBL      = 0x13D
BTN_THUMBR      = 0x13E

BTN_DPAD_UP     = 0x220
BTN_DPAD_DOWN   = 0x221
BTN_DPAD_LEFT   = 0x222
BTN_DPAD_RIGHT  = 0x223

# Alternative DPAD mappings sometimes reported
BTN_DPAD_LEFT_ALT   = 0x2C0
BTN_DPAD_RIGHT_ALT  = 0x2C1
BTN_DPAD_UP_ALT     = 0x2C2
BTN_DPAD_DOWN_ALT   = 0x2C3

##########################################################
# Notes:
#  • Event types are bitmasks: JS_EVENT_INIT may be OR’ed
#    with JS_EVENT_AXIS or JS_EVENT_BUTTON.
#  • Axis and button codes depend on device capabilities.
#  • Use `event_type & JS_EVENT_INIT` to filter out
#    initialization events.
##########################################################

# Mapping: driver code constant -> controller event name used in the codebase.
# Add entries here when a new controller reports a code you want to translate
# to a canonical robot input name.
DRIVER_CODE_TO_ROBOT_NAMES = {
    # ───────────────
    # Axes
    # ───────────────
    AXIS_LX: "left_stick_x",  # 'lx'
    AXIS_LY: "left_stick_y",  # 'ly'
    AXIS_RZ: "right_stick_x",  # 'rz'
    AXIS_LZ: "right_stick_y",  # 'lz'
    AXIS_GAS: "right_trigger",  # 'gas'
    AXIS_BRAKE: "left_trigger",  # 'brake'
    AXIS_HAT0X: "dpad_horizontal",  # 'hat0x'
    AXIS_HAT0Y: "dpad_vertical",  # 'hat0y'
    # ───────────────
    # Buttons
    # ───────────────
    BTN_A: "a",
    BTN_B: "b",
    BTN_C: "c",
    BTN_X: "x",
    BTN_Y: "y",
    BTN_Z: "z",
    BTN_TL: "left_bumper",  # 'tl'
    BTN_TR: "right_bumper",  # 'tr'
    BTN_TL2: "left_trigger_button",  # 'tl2'
    BTN_TR2: "right_trigger_button",  # 'tr2'
    BTN_SELECT: "back",  # 'select'
    BTN_START: "start",
    BTN_MODE: "guide",  # 'mode'
    BTN_THUMBL: "left_stick_click",  # 'thumbl'
    BTN_THUMBR: "right_stick_click",  # 'thumbr'
}
