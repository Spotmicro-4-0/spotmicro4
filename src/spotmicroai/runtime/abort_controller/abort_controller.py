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
from spotmicroai.runtime.messaging import MessageBus, MessageTopic
import spotmicroai.runtime.queues as queues

log = Logger().setup_logger('Abort controller')


class AbortController:
    """Handles abort signals and GPIO for graceful shutdown."""

    _gpio_port: Optional[int] = None
    _config_provider: ConfigProvider = ConfigProvider()

    def __init__(self, message_bus: MessageBus):

        try:

            log.debug(labels.ABORT_STARTING_CONTROLLER)

            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            self._gpio_port = self._config_provider.get_abort_gpio_port()

            retries = 10
            while retries > 0:
                # Need to check if the pi user has access to the GPIO system during boot
                # This is an issue when running the program as a service in systemd
                try:
                    log.info(labels.ABORT_ATTEMPTING_GPIO)
                    GPIO.setmode(GPIO.BCM)
                    assert self._gpio_port is not None
                    GPIO.setup(self._gpio_port, GPIO.OUT)
                    log.info(labels.ABORT_GPIO_SUCCESS)
                    break
                except Exception as e:
                    log.warning(labels.ABORT_GPIO_WARNING, e)
                    time.sleep(2)
                    retries -= 1

                    if retries == 0:
                        log.error(labels.ABORT_GPIO_ERROR)
                        try:
                            self.abort()
                        finally:
                            sys.exit(1)

            self._message_bus = message_bus
            self.abort()
            self._message_bus.put(MessageTopic.LCD_SCREEN, queues.LCD_SCREEN_SHOW_ABORT_CONTROLLER_OK_ON)

        except Exception as e:
            log.error(labels.ABORT_INIT_ERROR, e)
            self._message_bus.put(MessageTopic.LCD_SCREEN, queues.LCD_SCREEN_SHOW_ABORT_CONTROLLER_NOK)
            try:
                self.abort()
            finally:
                sys.exit(1)

    def exit_gracefully(self, _signum, _frame):
        try:
            self.abort()
        finally:
            log.info(labels.ABORT_TERMINATED)
            sys.exit(0)

    def do_process_events_from_queues(self):

        try:
            while True:
                event = self._message_bus.get(MessageTopic.ABORT)

                if event == queues.ABORT_CONTROLLER_ACTION_ACTIVATE:
                    self.activate_servos()

                if event == queues.ABORT_CONTROLLER_ACTION_ABORT:
                    self.abort()

        except Exception as e:
            log.error(labels.ABORT_QUEUE_ERROR, e)
            sys.exit(1)

    def activate_servos(self):
        assert self._gpio_port is not None
        self._message_bus.put(MessageTopic.LCD_SCREEN, queues.LCD_SCREEN_SHOW_ABORT_CONTROLLER_OK_ON)
        GPIO.output(self._gpio_port, GPIO.LOW)

    def abort(self):
        assert self._gpio_port is not None
        self._message_bus.put(MessageTopic.LCD_SCREEN, queues.LCD_SCREEN_SHOW_ABORT_CONTROLLER_OK_OFF)
        GPIO.output(self._gpio_port, GPIO.HIGH)
