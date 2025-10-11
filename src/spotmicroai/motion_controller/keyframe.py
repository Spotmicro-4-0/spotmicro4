from dataclasses import dataclass, field
from spotmicroai.motion_controller.coordinate import Coordinate
from spotmicroai.singleton import Singleton

@dataclass
class Keyframe:
    """A class defining the positions of the 4 feet at a given point in time.

    Attributes:
        rear_left: The position of the left rear leg (FootCoordinate).
        rear_right: The position of the right rear leg (FootCoordinate).
        front_left: The position of the left front leg (FootCoordinate).
        front_right: The position of the right front leg (FootCoordinate).
    """

    rear_left: Coordinate = field(default_factory=Coordinate)
    rear_right: Coordinate = field(default_factory=Coordinate)
    front_left: Coordinate = field(default_factory=Coordinate)
    front_right: Coordinate = field(default_factory=Coordinate)

class KeyframeTransition(metaclass=Singleton):
    """A class representing a transition from a previous keyframe to a current keyframe.

    Attributes:
        current: The current keyframe (Keyframe).
        previous: The previous keyframe (Keyframe).
    """

    current: Keyframe
    previous: Keyframe

    def __init__(self):
        self.current = Keyframe()
        self.previous = Keyframe()

    def createNextKeyframe(self):
        """Copy the current keyframe to previous and reset current to default values."""
        self.previous = self.current
        self.current = Keyframe()
