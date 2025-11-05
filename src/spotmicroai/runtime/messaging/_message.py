from enum import Enum


class MessageTopic(Enum):
    ABORT = "abort"
    MOTION = "motion"
    LCD = "lcd_screen"
    REMOTE = "remote"
    TELEMETRY = "telemetry"


class MessageTopicStatus(Enum):
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


class LcdMessage:
    def __init__(self, topic: MessageTopic, status: MessageTopicStatus):
        self.topic = topic
        self.status = status
