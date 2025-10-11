from typing import List
from spotmicroai.motion_controller.coordinate import Coordinate
from spotmicroai.singleton import Singleton
from spotmicroai.utilities.config import Config


class WalkingCycle(metaclass=Singleton):
    """A singleton class containing a predefined walking cycle for a single foot.

    Attributes:
        values: A list of FootCoordinate instances representing the cycle.
    """

    values: List[Coordinate]

    def __init__(self):
        config = Config()
        walking_cycle_data = config.get(Config.MOTION_CONTROLLER_WALKING_CYCLE)
        
        self.values = [Coordinate(*pos) for pos in walking_cycle_data]
