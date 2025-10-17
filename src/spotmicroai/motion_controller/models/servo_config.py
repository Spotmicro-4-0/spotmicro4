from dataclasses import dataclass


@dataclass
class ServoConfig:
    """A class with variables that hold the static configurations of the servo.

    These configurations are predefined and configured in the spotmicroai.json file,
    and do not change during runtime. This class carries these static values
    for each servo, providing immutable settings used throughout the application.

    Used to track the configurations of a servo

    Attributes:
        channel: The channel number on the PCA9685 connected to the servo
        min_pulse: The minimum pulse width in microseconds
        max_pulse: The maximum pulse width in microseconds
        rest_angle: The value of the resting angle of the servo
    """

    channel: int
    min_pulse: int
    max_pulse: int
    rest_angle: float
