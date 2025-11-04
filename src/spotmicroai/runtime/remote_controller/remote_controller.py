import signal
import sys
import time

from spotmicroai import labels
from spotmicroai.configuration._config_provider import ConfigProvider
from spotmicroai.constants import DEVICE_SEARCH_INTERVAL, PUBLISH_RATE_HZ, READ_LOOP_SLEEP
from spotmicroai.logger import Logger
from spotmicroai.runtime.messaging import MessageBus, MessageTopic
import spotmicroai.runtime.queues as queues

from .remote_control_service import RemoteControlService

log = Logger().setup_logger('Remote controller')


class RemoteControllerController:
    _config_provider = ConfigProvider()

    def __init__(self, message_bus: MessageBus):
        try:
            log.debug(labels.REMOTE_STARTING_CONTROLLER)

            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            # Get device name from config
            device_name = self._config_provider.get_remote_controller_device()

            # Initialize the remote control service
            self._remote_control_service = RemoteControlService(device_name)

            self._message_bus = message_bus

        except Exception as e:
            self._message_bus.put(MessageTopic.LCD_SCREEN, queues.LCD_SCREEN_SHOW_REMOTE_CONTROLLER_CONTROLLER_NOK)
            log.error(labels.REMOTE_INIT_ERROR.format(e))
            sys.exit(1)

    def exit_gracefully(self, _signum, _frame):
        log.info(labels.REMOTE_TERMINATED)
        sys.exit(0)

    def _notify_remote_controller_connected(self) -> None:
        """Notify LCD screen that remote controller has been connected."""
        self._message_bus.put(MessageTopic.LCD_SCREEN, queues.LCD_SCREEN_CONTROLLER_ACTION_ON)
        self._message_bus.put(MessageTopic.LCD_SCREEN, queues.LCD_SCREEN_SHOW_REMOTE_CONTROLLER_CONTROLLER_OK)

    def _notify_searching_for_device(self) -> None:
        """Notify about device search and abort current motion."""
        self._message_bus.put(MessageTopic.ABORT, queues.ABORT_CONTROLLER_ACTION_ABORT)
        self._message_bus.put(MessageTopic.LCD_SCREEN, queues.LCD_SCREEN_SHOW_REMOTE_CONTROLLER_CONTROLLER_SEARCHING)
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
                        self._message_bus.put(MessageTopic.MOTION, current_state)
                        last_publish_time = now

                    time.sleep(READ_LOOP_SLEEP)

                except Exception as e:
                    log.error(labels.REMOTE_QUEUE_ERROR.format(e))
                    self._message_bus.put(MessageTopic.ABORT, queues.ABORT_CONTROLLER_ACTION_ABORT)
                    remote_controller_connected_already = False
                    self._remote_control_service.disconnect()
                    break
