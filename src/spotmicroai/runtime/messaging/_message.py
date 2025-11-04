from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class MessageTopic(Enum):
    ABORT = "abort"
    MOTION = "motion"
    LCD_SCREEN = "lcd_screen"
    REMOTE = "remote"
    TELEMETRY = "telemetry"


class MessageControllerStatus(Enum):
    """Enum for controller status values."""

    ON = "ON"
    OFF = "OFF"
    OK = "OK"
    NOK = "NOK"
    SEARCHING = "SEARCHING"


class MessageAbortCommand(Enum):
    """Enum for controller status values."""

    ACTIVATE = "activate"
    ABORT = "abort"


class MessagePayload(ABC):
    """Base class for all message payloads. Ensures type safety across topics."""


@dataclass
class LcdScreenMessagePayload(MessagePayload):
    """Payload for LCD_SCREEN topic (string status messages)."""

    name: MessageTopic
    status: MessageControllerStatus

    def __init__(self, name: MessageTopic, controller_status: MessageControllerStatus) -> None:
        """Initialize LCD screen payload with validation."""
        self.name = name
        self.status = controller_status


@dataclass
class AbortMessagePayload(MessagePayload):
    """Payload for ABORT topic (action commands)."""

    command: MessageAbortCommand

    def __init__(self, command: MessageAbortCommand) -> None:
        """Initialize the abort controller payload."""
        self.command = command


@dataclass
class MotionMessagePayload(MessagePayload):
    """Payload for MOTION topic (joystick state)."""

    state: Dict[str, Any]

    def __init__(self, state: Optional[Dict[str, Any]] = None) -> None:
        """Initialize motion payload."""
        self.state = state or {}


@dataclass
class TelemetryMessagePayload(MessagePayload):
    """Payload for TELEMETRY topic (system metrics)."""

    data: Dict[str, Any]

    def __init__(self, data: Dict[str, Any]) -> None:
        """Initialize telemetry payload."""
        self.data = data
