from dataclasses import dataclass, field
from spotmicroai.motion_controller.models.coordinate import Coordinate


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