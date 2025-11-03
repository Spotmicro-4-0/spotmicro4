import multiprocessing
from typing import Any, Dict, Optional

from spotmicroai.runtime.messaging._message_topic import MessageTopic


class MessageBus:
    """Centralized holder for all inter-controller communication queues."""

    def __init__(self) -> None:
        self._queues: Dict[MessageTopic, multiprocessing.Queue] = {
            MessageTopic.ABORT: multiprocessing.Queue(10),
            MessageTopic.MOTION: multiprocessing.Queue(1),
            MessageTopic.GAIT: multiprocessing.Queue(10),
            MessageTopic.LCD_SCREEN: multiprocessing.Queue(10),
            MessageTopic.TELEMETRY: multiprocessing.Queue(10),
        }

    def put(
        self,
        topic: MessageTopic,
        payload: Any,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        self._queues[topic].put(payload, block=block, timeout=timeout)

    def get(
        self,
        topic: MessageTopic,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> Any:
        return self._queues[topic].get(block=block, timeout=timeout)

    def close(self) -> None:
        """Clean up all queues by closing them and joining their threads."""
        for queue in self._queues.values():
            queue.close()
            queue.join_thread()

    def __del__(self) -> None:
        self.close()
