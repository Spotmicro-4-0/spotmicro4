"""
This module defines the ControllerEvent dataclass for handling controller inputs.
"""

from dataclasses import dataclass
from enum import Enum


class ControllerEventKey(str, Enum):
    # --- Thumbsticks (analog) ---
    LEFT_STICK_X = "lx"  # Left thumbstick left/right
    LEFT_STICK_Y = "ly"  # Left thumbstick up/down
    RIGHT_STICK_Y = "lz"  # Right thumbstick up/down
    RIGHT_STICK_X = "rz"  # Right thumbstick left/right

    # --- Triggers (analog) ---
    RIGHT_TRIGGER = "gas"  # Right analog trigger
    LEFT_TRIGGER = "brake"  # Left analog trigger

    # --- D-Pad (HAT axes) ---
    DPAD_HORIZONTAL = "hat0x"  # -1 = left, +1 = right
    DPAD_VERTICAL = "hat0y"  # -1 = up, +1 = down

    # --- Face Buttons ---
    A = "a"
    B = "b"
    X = "x"
    Y = "y"

    # --- Bumpers & System Buttons ---
    LEFT_BUMPER = "tl"  # Left bumper button
    RIGHT_BUMPER = "tr"  # Right bumper button
    BACK = "select"  # 'Select' on PS / 'Back' or 'View' on Xbox
    START = "start"  # 'Start' / 'Menu' button
    LEFT_STICK_CLICK = "thumbl"  # Pressing left thumbstick (L3)
    RIGHT_STICK_CLICK = "thumbr"  # Pressing right thumbstick (R3)


@dataclass
class ControllerEvent:
    """
    Represents a controller event with inputs from thumbsticks, triggers, D-Pad, buttons, etc.

    Attributes are initialized from a dictionary containing controller input values.
    """

    # Thumbsticks (analog, -1.0 to 1.0)
    left_stick_x: float
    left_stick_y: float
    right_stick_x: float
    right_stick_y: float

    # Triggers (analog, 0.0 to 1.0)
    right_trigger: float
    left_trigger: float

    # D-Pad (digital, -1/0/1)
    dpad_horizontal: int
    dpad_vertical: int

    # Face buttons (digital, True/False)
    a: bool
    b: bool
    x: bool
    y: bool

    # Bumpers & system buttons (digital, True/False)
    left_bumper: bool
    right_bumper: bool
    back: bool
    start: bool
    left_stick_click: bool
    right_stick_click: bool

    def __init__(self, event_dict: dict):
        # Initialize from the incoming dict, with defaults
        self.left_stick_x = event_dict.get(ControllerEventKey.LEFT_STICK_X, 0.0)
        self.left_stick_y = event_dict.get(ControllerEventKey.LEFT_STICK_Y, 0.0)
        self.right_stick_x = event_dict.get(ControllerEventKey.RIGHT_STICK_X, 0.0)
        self.right_stick_y = event_dict.get(ControllerEventKey.RIGHT_STICK_Y, 0.0)
        self.right_trigger = event_dict.get(ControllerEventKey.RIGHT_TRIGGER, 0.0)
        self.left_trigger = event_dict.get(ControllerEventKey.LEFT_TRIGGER, 0.0)
        self.dpad_horizontal = event_dict.get(ControllerEventKey.DPAD_HORIZONTAL, 0)
        self.dpad_vertical = event_dict.get(ControllerEventKey.DPAD_VERTICAL, 0)
        self.a = event_dict.get(ControllerEventKey.A, False)
        self.b = event_dict.get(ControllerEventKey.B, False)
        self.x = event_dict.get(ControllerEventKey.X, False)
        self.y = event_dict.get(ControllerEventKey.Y, False)
        self.left_bumper = event_dict.get(ControllerEventKey.LEFT_BUMPER, False)
        self.right_bumper = event_dict.get(ControllerEventKey.RIGHT_BUMPER, False)
        self.back = event_dict.get(ControllerEventKey.BACK, False)
        self.start = event_dict.get(ControllerEventKey.START, False)
        self.left_stick_click = event_dict.get(ControllerEventKey.LEFT_STICK_CLICK, False)
        self.right_stick_click = event_dict.get(ControllerEventKey.RIGHT_STICK_CLICK, False)
