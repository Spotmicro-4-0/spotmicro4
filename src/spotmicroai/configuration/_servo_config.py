from dataclasses import dataclass


@dataclass
class ServoConfig:
    """Servo configuration dataclass"""

    channel: int
    min_pulse: int
    max_pulse: int
