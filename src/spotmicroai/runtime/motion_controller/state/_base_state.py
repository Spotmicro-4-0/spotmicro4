from abc import ABC, abstractmethod
from enum import Enum

from spotmicroai.logger import Logger


class RobotState(Enum):
    IDLE = 'idle'
    STAND = 'stand'
    WALK = 'walk'
    TRANSIT_IDLE = 'transit_idle'
    TRANSIT_STAND = 'transit_stand'


class BaseRobotState(ABC):
    _log = Logger().setup_logger('RobotState')

    @abstractmethod
    def enter(self) -> None:
        pass

    @abstractmethod
    def update(self) -> None:
        pass

    @abstractmethod
    def handle_event(self, event: dict) -> RobotState | None:
        pass

    @abstractmethod
    def exit(self) -> None:
        pass
