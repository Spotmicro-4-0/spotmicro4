from enum import auto, Enum


class State(Enum):
    IDLE = auto()
    TRANSIT_IDLE = auto()
    STAND = auto()
    TRANSIT_STAND = auto()
    WALK = auto()


class StateMachine:
    def __init__(self) -> None:
        self._current_state: State = State.IDLE

    @property
    def current_state(self) -> State:
        return self._current_state

    @current_state.setter
    def current_state(self, state: State) -> None:
        self._current_state = state
