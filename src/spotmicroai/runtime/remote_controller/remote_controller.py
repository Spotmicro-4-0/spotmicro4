import signal
import sys
import time

from spotmicroai import labels
from spotmicroai.configuration._config_provider import ConfigProvider
from spotmicroai.constants import DEVICE_SEARCH_INTERVAL, PUBLISH_RATE_HZ, READ_LOOP_SLEEP
from spotmicroai.logger import Logger
from spotmicroai.runtime.messaging import LcdMessage, MessageAbortCommand, MessageBus, MessageTopic, MessageTopicStatus
from spotmicroai.singleton import Singleton

from .remote_control_service import RemoteControlService

log = Logger().setup_logger('Remote controller')


class RemoteControllerController(metaclass=Singleton):
    _config_provider = ConfigProvider()

    def __init__(self):
        try:
            log.debug(labels.REMOTE_STARTING_CONTROLLER)

            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            # Get device name from config
            device_name = self._config_provider.get_remote_controller_device()

            # Initialize the remote control service
            self._remote_control_service = RemoteControlService(device_name)

            message_bus = MessageBus()
            self._lcd_topic = message_bus.lcd
            self._abort_topic = message_bus.abort
            self._motion_topic = message_bus.motion

        except Exception as e:
            self._lcd_topic.put(LcdMessage(MessageTopic.REMOTE, MessageTopicStatus.NOK))
            log.error(labels.REMOTE_INIT_ERROR.format(e))
            sys.exit(1)

    def exit_gracefully(self, _signum, _frame):
        log.info(labels.REMOTE_TERMINATED)
        sys.exit(0)

    def _notify_remote_controller_connected(self) -> None:
        """Notify LCD screen that remote controller has been connected."""
        self._lcd_topic.put(LcdMessage(MessageTopic.LCD, MessageTopicStatus.OK))
        self._lcd_topic.put(LcdMessage(MessageTopic.REMOTE, MessageTopicStatus.OK))

    def _notify_searching_for_device(self) -> None:
        """Notify about device search and abort current motion."""
        self._abort_topic.put(MessageAbortCommand.ABORT)
        self._lcd_topic.put(LcdMessage(MessageTopic.REMOTE, MessageTopicStatus.SEARCHING))

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
                self._remote_control_service.scan()
                time.sleep(DEVICE_SEARCH_INTERVAL)
                remote_controller_connected_already = False
                continue

            next_publish_time = time.time() + 1.0 / PUBLISH_RATE_HZ

            # Main event loop
            while True:
                try:
                    # Poll joystick events (~100 Hz)
                    self._remote_control_service.poll_events()

                    now = time.time()
                    if now >= next_publish_time:
                        # Publish the aggregated state
                        current_state = self._remote_control_service.controller_event()
                        self._motion_topic.put(current_state)

                        # Reset aggregated state so next window starts clean
                        self._remote_control_service.clear()

                        # Schedule next publish tick (avoids drift)
                        next_publish_time += 1.0 / PUBLISH_RATE_HZ

                    # Sleep briefly to limit CPU usage
                    time.sleep(READ_LOOP_SLEEP)

                except (OSError, IOError) as e:
                    # Recoverable hardware or I/O error: attempt reconnect
                    log.warning(labels.REMOTE_IO_ERROR.format(e))
                    self._remote_control_service.disconnect()
                    remote_controller_connected_already = False
                    break

                except Exception as e:
                    # Unexpected fatal exception: log and abort system
                    log.error(labels.REMOTE_QUEUE_ERROR.format(e))
                    self._abort_topic.put(MessageAbortCommand.ABORT)
                    self._remote_control_service.disconnect()
                    remote_controller_connected_already = False
                    break
