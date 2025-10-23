"""
This module provides the AbortController class for handling shutdown signals.
"""

import signal
import sys
import time
from typing import Optional

import RPi.GPIO as GPIO  # type: ignore

from spotmicroai.configuration import ConfigProvider
from spotmicroai.logger import Logger
import spotmicroai.runtime.queues as queues

log = Logger().setup_logger('Abort controller')


class AbortController:
    """Handles abort signals and GPIO for graceful shutdown."""

    _gpio_port: Optional[int] = None
    _config_provider: ConfigProvider = ConfigProvider()

    def __init__(self, communication_queues):

        try:

            log.debug('Starting controller...')

            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            self._gpio_port = self._config_provider.get_abort_gpio_port()

            retries = 10
            while retries > 0:
                # Need to check if the pi user has access to the GPIO system during boot
                # This is an issue when running the program as a service in systemd
                try:
                    log.info('Attempting to configure GPIO pins')
                    GPIO.setmode(GPIO.BCM)
                    assert self._gpio_port is not None
                    GPIO.setup(self._gpio_port, GPIO.OUT)
                    log.info('GPIO pins configured successfully.')
                    break
                except Exception as e:
                    log.warning(
                        'An error occured while attempting to access the GPIO pins. Will retry in 2 seconds.', e
                    )
                    time.sleep(2)
                    retries -= 1

                    if retries == 0:
                        log.error('Unable to access GPIO pins to configure the abort controller.')
                        try:
                            self.abort()
                        finally:
                            sys.exit(1)

            self._abort_queue = communication_queues[queues.ABORT_CONTROLLER]
            self._lcd_screen_queue = communication_queues[queues.LCD_SCREEN_CONTROLLER]

            self.abort()

            self._lcd_screen_queue.put(queues.LCD_SCREEN_SHOW_ABORT_CONTROLLER_OK_ON)

        except Exception as e:
            log.error('Abort controller initialization problem', e)
            self._lcd_screen_queue.put(queues.LCD_SCREEN_SHOW_ABORT_CONTROLLER_NOK)
            try:
                self.abort()
            finally:
                sys.exit(1)

    def exit_gracefully(self, _signum, _frame):
        try:
            self.abort()
        finally:
            log.info('Terminated')
            sys.exit(0)

    def do_process_events_from_queue(self):

        try:
            while True:
                event = self._abort_queue.get()

                if event == queues.ABORT_CONTROLLER_ACTION_ACTIVATE:
                    self.activate_servos()

                if event == queues.ABORT_CONTROLLER_ACTION_ABORT:
                    self.abort()

        except Exception as e:
            log.error('Unknown problem while processing the queue of the abort controller', e)
            sys.exit(1)

    def activate_servos(self):
        assert self._gpio_port is not None
        self._lcd_screen_queue.put(queues.LCD_SCREEN_SHOW_ABORT_CONTROLLER_OK_ON)
        GPIO.output(self._gpio_port, GPIO.LOW)

    def abort(self):
        assert self._gpio_port is not None
        self._lcd_screen_queue.put(queues.LCD_SCREEN_SHOW_ABORT_CONTROLLER_OK_OFF)
        GPIO.output(self._gpio_port, GPIO.HIGH)
