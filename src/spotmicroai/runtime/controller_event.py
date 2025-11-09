"""
This module defines the ControllerEvent dataclass for handling controller inputs.
"""

from dataclasses import dataclass

@dataclass
class ControllerEvent:
    """Represents either a full or partial controller update."""
    # Thumbsticks (analog)
    left_stick_x: float = 0.0
    left_stick_y: float = 0.0
    right_stick_x: float = 0.0
    right_stick_y: float = 0.0

    # Triggers (analog)
    right_trigger: float = 0.0
    left_trigger: float = 0.0

    # D-Pad (digital)
    dpad_horizontal: int = 0
    dpad_vertical: int = 0

    # Face buttons (digital)
    a: bool = False
    b: bool = False
    x: bool = False
    y: bool = False

    # Bumpers & system buttons (digital)
    left_bumper: bool = False
    right_bumper: bool = False
    back: bool = False
    start: bool = False
    left_stick_click: bool = False
    right_stick_click: bool = False
