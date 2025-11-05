from enum import Enum
import multiprocessing

from spotmicroai.singleton import Singleton


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


class MessageBus(metaclass=Singleton):
    """Centralized holder for all inter-controller communication queues."""

    _abort: multiprocessing.Queue
    _motion: multiprocessing.Queue
    _lcd: multiprocessing.Queue
    _telemetry: multiprocessing.Queue

    def __init__(self) -> None:
        self._abort = multiprocessing.Queue(10)
        self._motion = multiprocessing.Queue(1)
        self._lcd = multiprocessing.Queue(10)
        self._telemetry = multiprocessing.Queue(10)

    @property
    def abort(self):
        return self._abort

    @property
    def motion(self):
        return self._motion

    @property
    def lcd(self):
        return self._lcd

    @property
    def telemetry(self):
        return self._telemetry

    def get_queue_stats(self) -> dict[str, int]:
        """Return current message count for each queue."""
        return {
            "abort": self._abort.qsize(),
            "motion": self._motion.qsize(),
            "lcd": self._lcd.qsize(),
            "telemetry": self._telemetry.qsize(),
        }

    def log_queue_stats(self) -> None:
        """Log current queue statistics for debugging."""
        stats = self.get_queue_stats()
        print(f"MessageBus stats: {stats}")

    def close(self) -> None:
        """Clean up all queues by closing them and joining their threads."""
        self._abort.close()
        self._abort.join_thread()

        self._motion.close()
        self._motion.join_thread()

        self._lcd.close()
        self._lcd.join_thread()

        self._telemetry.close()
        self._telemetry.join_thread()

    def __del__(self) -> None:
        self.close()
