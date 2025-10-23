"""
This module defines the ControllerEvent dataclass for handling controller inputs.
"""

from dataclasses import dataclass


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
        self.left_stick_x = event_dict.get('lx', 0.0)
        self.left_stick_y = event_dict.get('ly', 0.0)
        self.right_stick_x = event_dict.get('rz', 0.0)
        self.right_stick_y = event_dict.get('lz', 0.0)
        self.right_trigger = event_dict.get('gas', 0.0)
        self.left_trigger = event_dict.get('brake', 0.0)
        self.dpad_horizontal = event_dict.get('hat0x', 0)
        self.dpad_vertical = event_dict.get('hat0y', 0)
        self.a = event_dict.get('a', False)
        self.b = event_dict.get('b', False)
        self.x = event_dict.get('x', False)
        self.y = event_dict.get('y', False)
        self.left_bumper = event_dict.get('tl', False)
        self.right_bumper = event_dict.get('tr', False)
        self.back = event_dict.get('select', False)
        self.start = event_dict.get('start', False)
        self.left_stick_click = event_dict.get('thumbl', False)
        self.right_stick_click = event_dict.get('thumbr', False)
