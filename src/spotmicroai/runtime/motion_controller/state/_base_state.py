from abc import ABC, abstractmethod
from enum import Enum

from spotmicroai.logger import Logger
from spotmicroai.runtime.motion_controller.models import ControllerEvent


class RobotStateName(Enum):
    IDLE = 'idle'
    STAND = 'stand'
    WALK = 'walk'
    TRANSIT_IDLE = 'transit_idle'
    TRANSIT_STAND = 'transit_stand'


class BaseRobotState(ABC):
    _log = Logger().setup_logger('BaseRobotState')

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
