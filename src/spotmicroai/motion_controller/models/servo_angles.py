from dataclasses import dataclass


@dataclass
class ServoAngles:
    """A class that holds three servo angles: shoulder_angle, leg_angle, and foot_angle.

    Used to describe the angles for servo motors.

    Attributes:
        shoulder_angle: The shoulder angle (float).
        leg_angle: The leg angle (float).
        foot_angle: The foot angle (float).
    """

    shoulder_angle: float = 90.0
    leg_angle: float = 90.0
    foot_angle: float = 90.0
