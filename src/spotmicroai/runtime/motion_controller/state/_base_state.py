from abc import ABC, abstractmethod
from enum import Enum

from spotmicroai import constants
from spotmicroai.logger import Logger
from spotmicroai.runtime.controller_event import ControllerEvent


class RobotStateName(Enum):
    IDLE = 'idle'
    STAND = 'stand'
    WALK = 'walk'
    TRANSIT_IDLE = 'transit_idle'
    TRANSIT_STAND = 'transit_stand'


class BaseRobotState(ABC):
    _log = Logger().setup_logger('BaseRobotState')

    @property
    def frame_duration(self) -> float:
        """Return the frame duration for this state in seconds. Override in subclasses if different from default."""
        return constants.FRAME_DURATION

    @abstractmethod
    def enter(self) -> None:
        pass

    @abstractmethod
    def update(self) -> None:
        pass

    @abstractmethod
    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        pass

    @abstractmethod
    def exit(self) -> None:
        pass
