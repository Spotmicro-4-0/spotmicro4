from multiprocessing import Queue
import os
import queue
import re
import signal
import sys
import time

from spotmicroai import labels
from spotmicroai.configuration._config_provider import ConfigProvider
from spotmicroai.constants import (
    CUSTOM_ICONS,
    ICON_EMPTY,
    ICON_GPIO,
    ICON_PCA9685,
    ICON_PROBLEM,
    ICON_REMOTE_CONTROLLER,
    ICON_SUCCESS,
    ICON_SUCCESS_REVERSE,
    ICON_TEMPERATURE,
    LCD_CURSOR_BEGIN_LINE_2,
    LCD_CURSOR_BEING_LINE_1,
    LCD_DECIMAL_WRITE_MODE,
)
from spotmicroai.hardware.lcd_display import Lcd16x2
from spotmicroai.logger import Logger
from spotmicroai.runtime.messaging import MessageBus, MessageTopic, MessageTopicStatus
from spotmicroai.singleton import Singleton

log = Logger().setup_logger('LcdScreenController')

LCD_DISPLAY_TEXT = 'Spotmicro'


class LcdScreenController(metaclass=Singleton):
    _is_alive: bool
    _config_provider: ConfigProvider = ConfigProvider()

    _lcd_status: MessageTopicStatus | None
    _abort_status: MessageTopicStatus | None
    _remote_controller_status: MessageTopicStatus | None
    _motion_status: MessageTopicStatus | None
    _screen: Lcd16x2
    _lcd_topic: Queue

    def __init__(self, message_bus: MessageBus):
        try:

            log.debug(labels.LCD_STARTING_CONTROLLER)

            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            i2c_address = self._config_provider.get_lcd_screen_address()

            self.screen = Lcd16x2(address=i2c_address)

            self._lcd_topic = message_bus.lcd
            self._lcd_status = None
            self._abort_status = None
            self._remote_controller_status = None
            self._motion_status = None
            self.screen.lcd_clear()
            self.turn_on()

            self.is_alive = True

        except Exception as e:
            self.is_alive = False
            log.error(labels.LCD_INIT_ERROR.format(e))

    def exit_gracefully(self, _signum, _frame):
        try:
            self.turn_off()
        finally:
            log.info(labels.LCD_TERMINATED)
            sys.exit(0)

    def do_process_events_from_queues(self) -> None:

        if not self.is_alive:
            log.error(labels.LCD_WORKING_WITHOUT)
            return

        try:
            while True:

                try:
                    message = self._lcd_topic.get(timeout=0.2)

                    if message.topic == MessageTopic.LCD:
                        self._lcd_status = message.status

                    elif message.topic == MessageTopic.ABORT:
                        self._abort_status = message.status

                    elif message.topic == MessageTopic.REMOTE:
                        self._remote_controller_status = message.status

                    elif message.topic == MessageTopic.MOTION:
                        self._motion_status = message.status

                except queue.Empty:
                    self.update_lcd_screen()

        except Exception as e:
            log.error(labels.LCD_QUEUE_ERROR.format(e))

    def turn_off(self):
        self.screen.lcd_clear()
        time.sleep(0.2)
        self.screen.backlight(0)

    def turn_on(self):
        self.screen.backlight(1)

    def update_lcd_screen(self):

        self._toggle_lcd()
        self.screen.lcd_load_custom_chars(CUSTOM_ICONS.values())
        self._write_first_line()
        self._write_second_line()

    def _toggle_lcd(self) -> None:
        if self._lcd_status == MessageTopicStatus.ON:
            self.turn_on()
        elif self._lcd_status == MessageTopicStatus.OFF:
            self.turn_off()

    def _write_status_icon(self, status: MessageTopicStatus | None) -> None:
        if status == MessageTopicStatus.OK or status == MessageTopicStatus.ON:
            char = ICON_SUCCESS
        elif status == MessageTopicStatus.SEARCHING:
            char = ICON_SUCCESS_REVERSE
        else:
            char = ICON_PROBLEM
        self.screen.lcd_write_char(char)

    def _write_first_line(self) -> None:
        self.screen.lcd_write(LCD_CURSOR_BEING_LINE_1)
        for char in LCD_DISPLAY_TEXT:
            self.screen.lcd_write(ord(char), LCD_DECIMAL_WRITE_MODE)

        self.screen.lcd_write_char(ICON_EMPTY)
        self.screen.lcd_write_char(ICON_EMPTY)
        self.screen.lcd_write_char(ICON_REMOTE_CONTROLLER)
        self.screen.lcd_write_char(ICON_EMPTY)
        self.screen.lcd_write_char(ICON_GPIO)
        self.screen.lcd_write_char(ICON_EMPTY)
        self.screen.lcd_write_char(ICON_PCA9685)

    def _write_second_line(self) -> None:
        self.screen.lcd_write(LCD_CURSOR_BEGIN_LINE_2)
        self._write_temperature()
        self.screen.lcd_write_char(ICON_EMPTY)
        self.screen.lcd_write_char(ICON_EMPTY)
        self.screen.lcd_write_char(ICON_EMPTY)
        self.screen.lcd_write_char(ICON_EMPTY)
        self.screen.lcd_write_char(ICON_EMPTY)

        self._write_status_icon(self._remote_controller_status)
        self.screen.lcd_write_char(ICON_EMPTY)
        self._write_status_icon(self._abort_status)
        self.screen.lcd_write_char(ICON_EMPTY)
        self._write_status_icon(self._motion_status)

    def _write_temperature(self) -> None:
        temperature = None
        try:
            temp_output = os.popen("vcgencmd measure_temp").readline()
            match = re.search(r"[-+]?\d*\.\d+|\d+", temp_output)
            if match:
                temperature = match.group()
        except Exception as e:
            log.error(labels.LCD_TEMP_ERROR.format(e))

        if temperature:
            for char in temperature:
                self.screen.lcd_write(ord(char), LCD_DECIMAL_WRITE_MODE)
            self.screen.lcd_write_char(ICON_TEMPERATURE)
            remaining = 5 - len(temperature)
            for _ in range(remaining):
                self.screen.lcd_write_char(ICON_EMPTY)
        else:
            for _ in range(6):
                self.screen.lcd_write_char(ICON_EMPTY)
