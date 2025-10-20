import os
import queue
import signal
import sys
import time

from spotmicroai.core.lcd_screen_controller.lcd_16x2 import Lcd16x2
from spotmicroai.core.utilities.config import Config
from spotmicroai.core.utilities.log import Logger
import spotmicroai.core.utilities.queues as queues

log = Logger().setup_logger('LCD Screen controller')


class LCDScreenController:
    is_alive = False
    config = Config()

    lcd_screen_controller = None
    abort_controller = None
    remote_controller_controller = None
    motion_controller = None

    def __init__(self, communication_queues):
        try:

            log.debug('Starting controller...')

            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            i2c_address = int(self.config.lcd_screen_controller.address, 0)

            self.screen = Lcd16x2(address=i2c_address)

            self._lcd_screen_queue = communication_queues[queues.LCD_SCREEN_CONTROLLER]
            self.screen.lcd_clear()
            self.update_lcd_creen()
            self.turn_on()

            self.is_alive = True

        except Exception as e:
            self.is_alive = False
            log.error('LCD Screen controller initialization problem, module not critical, skipping: %s', e)

    def exit_gracefully(self, _signum, _frame):
        try:
            self.turn_off()
        finally:
            log.info('Terminated')
            sys.exit(0)

    def do_process_events_from_queue(self):

        if not self.is_alive:
            log.error("SpotMicro is working without LCD Screen")
            return

        try:
            while True:

                try:
                    event = self._lcd_screen_queue.get(block=True, timeout=1)

                    if event.startswith(queues.LCD_SCREEN_CONTROLLER + ' '):
                        self.lcd_screen_controller = event[len(queues.LCD_SCREEN_CONTROLLER) + 1 :]

                    if event.startswith(queues.ABORT_CONTROLLER + ''):
                        self.abort_controller = event[len(queues.ABORT_CONTROLLER) + 1 :]

                    if event.startswith(queues.REMOTE_CONTROLLER_CONTROLLER + ' '):
                        self.remote_controller_controller = event[len(queues.REMOTE_CONTROLLER_CONTROLLER + ' ') :]

                    if event.startswith(queues.MOTION_CONTROLLER + ' '):
                        self.motion_controller = event[len(queues.MOTION_CONTROLLER + ' ') :]

                except queue.Empty:
                    self.update_lcd_creen()
                    time.sleep(1)

        except Exception as e:
            log.error('Unknown problem while processing the queue of the lcd screen controller: %s', e)

    def turn_off(self):
        self.screen.lcd_clear()
        time.sleep(0.1)
        self.screen.backlight(0)

    def turn_on(self):
        self.screen.backlight(1)

    def update_lcd_creen(self):  # https://www.quinapalus.com/hd44780udg.html

        if self.lcd_screen_controller == 'ON':
            self.turn_on()
        elif self.lcd_screen_controller == 'OFF':
            self.turn_off()

        temperature = self.temperature()

        custom_icons = []

        icon_empty = [0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
        icon_success = [0x0, 0x1, 0x3, 0x16, 0x1C, 0x8, 0x0, 0x0]
        icon_pca9685 = [0x1F, 0x11, 0x15, 0x15, 0x15, 0x15, 0x11, 0x1F]
        icon_gpio = [0x4, 0x4, 0x1F, 0x0, 0x0, 0xE, 0x4, 0x4]
        icon_remote_controller = [0x11, 0xA, 0xE, 0xA, 0xA, 0xE, 0xA, 0x11]
        icon_temperature = [0x18, 0x18, 0x3, 0x4, 0x4, 0x4, 0x3, 0x0]
        icon_problem = [0x0, 0x1B, 0xE, 0x4, 0xE, 0x1B, 0x0, 0x0]
        icon_success_reverse = [0x1F, 0x1E, 0x1C, 0x9, 0x3, 0x17, 0x1F]

        # There is only memory for 7 in the lcd screen controller
        custom_icons.insert(0, icon_empty)
        custom_icons.insert(1, icon_success)
        custom_icons.insert(2, icon_pca9685)
        custom_icons.insert(3, icon_gpio)
        custom_icons.insert(4, icon_remote_controller)
        custom_icons.insert(5, icon_temperature)
        custom_icons.insert(6, icon_problem)
        custom_icons.insert(7, icon_success_reverse)

        self.screen.lcd_load_custom_chars(custom_icons)

        self.screen.lcd_write(0x80)  # First line

        for char in 'SpotMicro':
            self.screen.lcd_write(ord(char), 0b00000001)

        self.screen.lcd_write_char(0)
        self.screen.lcd_write_char(4)
        self.screen.lcd_write_char(0)
        self.screen.lcd_write_char(3)
        self.screen.lcd_write_char(0)
        self.screen.lcd_write_char(2)
        self.screen.lcd_write_char(2)

        # Write next three chars to row 2 directly
        self.screen.lcd_write(0xC0)  # Second line
        self.screen.lcd_write_char(0)
        self.screen.lcd_write_char(0)
        self.screen.lcd_write_char(0)
        self.screen.lcd_write_char(0)
        self.screen.lcd_write_char(0)

        if temperature:
            for char in temperature.rjust(3, ' '):
                self.screen.lcd_write(ord(char), 0b00000001)
            self.screen.lcd_write_char(5)
        else:
            self.screen.lcd_write_char(0)
            self.screen.lcd_write_char(0)
            self.screen.lcd_write_char(0)
            self.screen.lcd_write_char(0)

        self.screen.lcd_write_char(0)

        if self.remote_controller_controller == 'OK':
            self.screen.lcd_write_char(1)
        elif self.remote_controller_controller == 'SEARCHING':
            self.screen.lcd_write_char(7)
        else:
            self.screen.lcd_write_char(6)

        self.screen.lcd_write_char(0)

        if self.abort_controller == 'OK ON':
            self.screen.lcd_write_char(1)
        elif self.abort_controller == 'OK OFF':
            self.screen.lcd_write_char(7)
        else:
            self.screen.lcd_write_char(6)

        self.screen.lcd_write_char(0)

        if self.motion_controller == 'OK':
            self.screen.lcd_write_char(1)
        else:
            self.screen.lcd_write_char(6)

    def temperature(self):
        try:
            temp = os.popen("vcgencmd measure_temp").readline()
            return temp.replace("temp=", "")[:-5]
        except Exception as e:
            log.error('Error reading system temperature: %s', e)
            return '000'
