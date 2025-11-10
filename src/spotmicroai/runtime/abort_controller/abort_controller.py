"""
This module provides the AbortController class for handling shutdown signals.
"""

import signal
import sys
import time
from typing import Optional

import RPi.GPIO as GPIO  # type: ignore

from spotmicroai import labels
from spotmicroai.configuration import ConfigProvider
from spotmicroai.logger import Logger
from spotmicroai.runtime.messaging import LcdMessage, MessageAbortCommand, MessageBus, MessageTopic, MessageTopicStatus
from spotmicroai.singleton import Singleton

log = Logger().setup_logger('Abort controller')


class AbortController(metaclass=Singleton):
    """Handles abort signals and GPIO for graceful shutdown."""

    _gpio_port: Optional[int] = None
    _config_provider: ConfigProvider = ConfigProvider()

    def __init__(self):

        try:

            log.debug(labels.ABORT_STARTING_CONTROLLER)

            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            self._gpio_port = self._config_provider.get_abort_gpio_port()
            message_bus = MessageBus()
            self._lcd_topic = message_bus.lcd
            self._abort_topic = message_bus.abort

            self._initialize_gpio()

            self.abort()
            self._lcd_topic.put(LcdMessage(MessageTopic.ABORT, MessageTopicStatus.ON))

        except Exception as e:
            log.error(labels.ABORT_INIT_ERROR, e)
            self._lcd_topic.put(LcdMessage(MessageTopic.ABORT, MessageTopicStatus.NOK))
            try:
                self.abort()
            finally:
                sys.exit(1)

    def _initialize_gpio(self, max_retries: int = 10, retry_delay: float = 2.0) -> None:
        """Initialize GPIO with retry logic for systemd service startup.

        When running as a systemd service, GPIO may not be immediately accessible.
        This method retries initialization to handle this race condition.
        """
        for attempt in range(1, max_retries + 1):
            try:
                log.info(labels.ABORT_ATTEMPTING_GPIO)
                GPIO.setmode(GPIO.BCM)
                assert self._gpio_port is not None
                GPIO.setup(self._gpio_port, GPIO.OUT)
                log.info(labels.ABORT_GPIO_SUCCESS)
                return
            except Exception as e:
                if attempt == max_retries:
                    log.error(labels.ABORT_GPIO_ERROR)
                    raise
                log.warning(labels.ABORT_GPIO_WARNING, e)
                time.sleep(retry_delay)

    def exit_gracefully(self, _signum, _frame):
        try:
            self.abort()
        finally:
            log.info(labels.ABORT_TERMINATED)
            sys.exit(0)

    def do_process_events_from_queues(self):

        try:
            while True:
                event = self._abort_topic.get()

                if event == MessageAbortCommand.ACTIVATE:
                    self.activate_servos()

                if event == MessageAbortCommand.ABORT:
                    self.abort()

        except Exception as e:
            log.error(labels.ABORT_QUEUE_ERROR, e)
            sys.exit(1)

    def activate_servos(self):
        assert self._gpio_port is not None
        self._lcd_topic.put(LcdMessage(MessageTopic.ABORT, MessageTopicStatus.ON))
        GPIO.output(self._gpio_port, GPIO.LOW)

    def abort(self):
        assert self._gpio_port is not None
        self._lcd_topic.put(LcdMessage(MessageTopic.ABORT, MessageTopicStatus.OFF))
        GPIO.output(self._gpio_port, GPIO.HIGH)
        time.sleep(0.1)
