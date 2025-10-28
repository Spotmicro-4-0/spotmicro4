import signal
import sys
import time

from spotmicroai.configuration._config_provider import ConfigProvider
from spotmicroai.logger import Logger
import spotmicroai.runtime.queues as queues
from .remote_control_service import RemoteControlService
from .remote_controller_constants import (
    PUBLISH_RATE_HZ,
    READ_LOOP_SLEEP,
    DEVICE_SEARCH_INTERVAL,
)

log = Logger().setup_logger('Remote controller')


class RemoteControllerController:
    _config_provider = ConfigProvider()

    def __init__(self, communication_queues):
        try:
            log.debug('Starting controller...')

            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            # Get device name from config
            device_name = self._config_provider.get_remote_controller_device()

            # Initialize the remote control service
            self._remote_control_service = RemoteControlService(device_name)

            self._abort_queue = communication_queues[queues.ABORT_CONTROLLER]
            self._motion_queue = communication_queues[queues.MOTION_CONTROLLER]
            self._lcd_screen_queue = communication_queues[queues.LCD_SCREEN_CONTROLLER]

        except Exception as e:
            self._lcd_screen_queue.put(queues.LCD_SCREEN_SHOW_REMOTE_CONTROLLER_CONTROLLER_NOK)
            log.error('Remote controller controller initialization problem: %s', e)
            sys.exit(1)

    def exit_gracefully(self, _signum, _frame):
        log.info('Terminated')
        sys.exit(0)

    def _notify_remote_controller_connected(self) -> None:
        """Notify LCD screen that remote controller has been connected."""
        self._lcd_screen_queue.put(queues.LCD_SCREEN_CONTROLLER_ACTION_ON)
        self._lcd_screen_queue.put(queues.LCD_SCREEN_SHOW_REMOTE_CONTROLLER_CONTROLLER_OK)

    def _notify_searching_for_device(self) -> None:
        """Notify about device search and abort current motion."""
        self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
        self._lcd_screen_queue.put(queues.LCD_SCREEN_SHOW_REMOTE_CONTROLLER_CONTROLLER_SEARCHING)
        self._remote_control_service.check_for_connected_devices()

    def do_process_events_from_queues(self):
        """
        Main event loop. Uses the RemoteControlService to read joystick events
        and publishes the state at a steady rate so that movement persists
        while the stick is held in position.
        """
        remote_controller_connected_already = False

        while True:
            if self._remote_control_service.is_connected and not remote_controller_connected_already:
                self._notify_remote_controller_connected()
                remote_controller_connected_already = True
            else:
                self._notify_searching_for_device()
                time.sleep(DEVICE_SEARCH_INTERVAL)
                remote_controller_connected_already = False
                continue

            last_publish_time = 0

            # Main event loop
            while True:
                try:
                    # Try to read and parse events from the device
                    self._remote_control_service.read_and_parse_events()

                    now = time.time()
                    if now - last_publish_time >= 1.0 / PUBLISH_RATE_HZ:
                        # Get current state and publish
                        current_state = self._remote_control_service.get_current_state()
                        self._motion_queue.put(current_state)
                        last_publish_time = now

                    time.sleep(READ_LOOP_SLEEP)

                except Exception as e:
                    log.error('Unknown problem while processing the queue of the remote controller: %s', e)
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
                    remote_controller_connected_already = False
                    self._remote_control_service.disconnect()
                    break
