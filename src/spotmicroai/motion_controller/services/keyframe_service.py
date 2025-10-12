from typing import List
from spotmicroai.motion_controller.models.coordinate import Coordinate
from spotmicroai.motion_controller.models.keyframe import Keyframe
from spotmicroai.singleton import Singleton
from spotmicroai.utilities.config import Config

class KeyframeService(metaclass=Singleton):
    """A class representing a transition from a previous keyframe to a current keyframe.

    Attributes:
        current: The current keyframe (Keyframe).
        previous: The previous keyframe (Keyframe).
    """
    walking_cycle: List[Coordinate] = []
    walking_cycle_length: int = 0
    current: Keyframe
    previous: Keyframe

    def __init__(self):
        self.current = Keyframe()
        self.previous = Keyframe()

        if not self.walking_cycle:
            config = Config()
            walking_cycle_data = config.get(Config.MOTION_CONTROLLER_WALKING_CYCLE)
            self.__class__.walking_cycle = [Coordinate(*pos) for pos in walking_cycle_data]
            self.__class__.walking_cycle_length = len(self.walking_cycle)

    def createNextKeyframe(self):
        """Copy the current keyframe to previous and reset current to default values."""
        self.previous = self.current
        self.current = Keyframe()