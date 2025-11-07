import queue
import signal
import sys
import time

from spotmicroai import labels
import spotmicroai.constants as constants
from spotmicroai.hardware.servo.servo_service import ServoService
from spotmicroai.logger import Logger
from spotmicroai.runtime.messaging import LcdMessage, MessageAbortCommand, MessageBus, MessageTopic, MessageTopicStatus
from spotmicroai.runtime.motion_controller.services import TelemetryService
from spotmicroai.runtime.motion_controller.state.state_machine import StateMachine
from spotmicroai.singleton import Singleton

log = Logger().setup_logger('Motion controller')


class MotionController(metaclass=Singleton):

    _servo_service: ServoService
    _telemetry_service: TelemetryService

    _state_machine: StateMachine
    _inactivity_counter: float

    def __init__(self, message_bus: MessageBus):
        try:
            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            self._servo_service = ServoService()
            self._telemetry_service = TelemetryService(self)

            self._motion_topic = message_bus.motion
            self._abort_topic = message_bus.abort
            self._lcd_topic = message_bus.lcd
            self._telemetry_topic = message_bus.telemetry

            self._inactivity_counter = time.time()

            self._state_machine = StateMachine()

            self._lcd_topic.put(LcdMessage(MessageTopic.MOTION, MessageTopicStatus.OK))

            time.sleep(constants.DEFAULT_SLEEP)

        except Exception as e:
            log.error(labels.MOTION_INIT_PROBLEM, e)
            self._lcd_topic.put(LcdMessage(MessageTopic.MOTION, MessageTopicStatus.OK))
            sys.exit(1)

    def exit_gracefully(self, _signum, _frame):
        """
        Handles graceful shutdown on signal reception, moving servos to rest and deactivating hardware.
        """
        log.info(labels.MOTION_GRACEFUL_SHUTDOWN)

        # Move servos to neutral (rest) first
        self._servo_service.rest_position()
        time.sleep(0.3)

        self._servo_service.deactivate_servos()

        self._abort_topic.put(MessageAbortCommand.ABORT)
        log.info(labels.MOTION_TERMINATED)
        sys.exit(0)

    def do_process_events_from_queues(self) -> None:
        telemetry_update_counter = 0

        while True:
            frame_start = time.time()

            event = self._get_controller_event()

            self._state_machine.handle_event(event)
            self._state_machine.update()

            self._servo_service.commit()

            elapsed_time = time.time() - frame_start
            self._update_telemetry(telemetry_update_counter, event, elapsed_time)
            telemetry_update_counter = (telemetry_update_counter + 1) % constants.TELEMETRY_UPDATE_INTERVAL

            self._sleep_until_next_frame(frame_start)

    def _get_controller_event(self) -> dict:
        try:
            return self._motion_topic.get(block=False)
        except queue.Empty:
            return {}

    def _update_telemetry(self, counter: int, event: dict, elapsed_time: float) -> None:
        if counter != 0:
            return

        loop_time_ms = elapsed_time * 1000
        idle_time_ms = max((constants.FRAME_DURATION - elapsed_time) * 1000, 0)

        try:
            telemetry_data = self._telemetry_service.collect(
                event=event,
                loop_time_ms=loop_time_ms,
                idle_time_ms=idle_time_ms,
                cycle_index=None,
                cycle_ratio=None,
                leg_positions=None,
            )
            try:
                self._telemetry_topic.put(telemetry_data, block=False)
            except queue.Full:
                log.debug(labels.MOTION_TELEMETRY_QUEUE_FULL)
        except Exception as e:
            log.warning(labels.MOTION_TELEMETRY_ERROR.format(e))

    def _sleep_until_next_frame(self, frame_start: float) -> None:
        elapsed = time.time() - frame_start
        if elapsed < constants.FRAME_DURATION:
            time.sleep(constants.FRAME_DURATION - elapsed)
