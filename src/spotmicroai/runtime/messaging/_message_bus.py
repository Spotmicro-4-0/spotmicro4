import multiprocessing
from typing import Dict, Literal, Optional, overload

# Import your actual concrete payload types
from spotmicroai.runtime.messaging._message import (
    AbortMessagePayload,
    LcdScreenMessagePayload,
    MessagePayload,
    MessageTopic,
    MotionMessagePayload,
    TelemetryMessagePayload,
)
from spotmicroai.singleton import Singleton


class MessageBus(metaclass=Singleton):
    """Centralized holder for all inter-controller communication queues."""

    def __init__(self) -> None:
        self._queues: Dict[MessageTopic, multiprocessing.Queue] = {
            MessageTopic.ABORT: multiprocessing.Queue(10),
            MessageTopic.MOTION: multiprocessing.Queue(1),
            MessageTopic.LCD_SCREEN: multiprocessing.Queue(10),
            MessageTopic.TELEMETRY: multiprocessing.Queue(10),
        }

    def put(
        self,
        topic: MessageTopic,
        payload: MessagePayload,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        self._queues[topic].put(payload, block=block, timeout=timeout)

    @overload
    def get(
        self,
        topic: Literal[MessageTopic.ABORT],
        *,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> AbortMessagePayload: ...
    @overload
    def get(
        self,
        topic: Literal[MessageTopic.MOTION],
        *,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> MotionMessagePayload: ...
    @overload
    def get(
        self,
        topic: Literal[MessageTopic.LCD_SCREEN],
        *,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> LcdScreenMessagePayload: ...
    @overload
    def get(
        self,
        topic: Literal[MessageTopic.TELEMETRY],
        *,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> TelemetryMessagePayload: ...
    @overload
    def get(
        self,
        topic: MessageTopic,
        *,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> MessagePayload: ...

    def get(
        self,
        topic: MessageTopic,
        *,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> MessagePayload:
        """Get a message from the queue for the given topic."""
        return self._queues[topic].get(block=block, timeout=timeout)

    def close(self) -> None:
        """Clean up all queues by closing them and joining their threads."""
        for queue in self._queues.values():
            queue.close()
            queue.join_thread()

    def __del__(self) -> None:
        self.close()
