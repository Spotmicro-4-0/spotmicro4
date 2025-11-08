import queue
import signal
import sys
import time

from spotmicroai import labels
import spotmicroai.constants as constants
from spotmicroai.hardware.buzzer.buzzer import Buzzer
from spotmicroai.hardware.servo.servo_service import ServoService
from spotmicroai.logger import Logger
from spotmicroai.runtime.messaging import LcdMessage, MessageAbortCommand, MessageBus, MessageTopic, MessageTopicStatus
from spotmicroai.runtime.motion_controller.models.controller_event import ControllerEvent
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
            self._telemetry_service = TelemetryService(self, message_bus)

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
        frame_count = 0
        total_get_event = 0.0
        total_handle_event = 0.0
        total_update = 0.0
        total_commit = 0.0

        while True:
            frame_start = time.time()

            t1 = time.time()
            event = self._get_controller_event()
            t2 = time.time()

            self._state_machine.handle_event(event)
            t3 = time.time()

            self._state_machine.update()
            t4 = time.time()

            self._servo_service.commit()
            t5 = time.time()

            elapsed_time = time.time() - frame_start
            idle_time = constants.FRAME_DURATION - elapsed_time

            # Accumulate timing stats
            frame_count += 1
            total_get_event += t2 - t1
            total_handle_event += t3 - t2
            total_update += t4 - t3
            total_commit += t5 - t4

            # Print stats every 50 frames
            if frame_count % 50 == 0:
                avg_stats = (
                    f"[Frame {frame_count}] Avg timing (ms): "
                    f"get={total_get_event/frame_count*1000:.2f} "
                    f"handle={total_handle_event/frame_count*1000:.2f} "
                    f"update={total_update/frame_count*1000:.2f} "
                    f"commit={total_commit/frame_count*1000:.2f} "
                    f"total={(total_get_event+total_handle_event+total_update+total_commit)/frame_count*1000:.2f}"
                )
                print(avg_stats, flush=True)

            if elapsed_time > constants.FRAME_DURATION:
                Buzzer().stop()
                breakdown = (
                    f"\n{'='*60}\n"
                    f"Frame timing breakdown:\n"
                    f"  get_event:     {(t2-t1)*1000:.2f}ms\n"
                    f"  handle_event:  {(t3-t2)*1000:.2f}ms\n"
                    f"  update:        {(t4-t3)*1000:.2f}ms\n"
                    f"  commit:        {(t5-t4)*1000:.2f}ms\n"
                    f"  TOTAL:         {elapsed_time*1000:.2f}ms (target: {constants.FRAME_DURATION*1000:.2f}ms)\n"
                    f"{'='*60}"
                )
                print(breakdown, file=sys.stderr, flush=True)
                log.error(breakdown)
                raise RuntimeError(
                    f"Frame execution exceeded duration: {elapsed_time:.4f}s > {constants.FRAME_DURATION}s"
                )

            self._publish_telemetry(event, elapsed_time, idle_time)
            self._sleep_until_next_frame(idle_time)

    def _get_controller_event(self) -> ControllerEvent:
        try:
            return self._motion_topic.get(block=False)
        except queue.Empty:
            return ControllerEvent({})

    def _publish_telemetry(self, event: ControllerEvent, elapsed_time: float, idle_time: float) -> None:
        loop_time_ms = elapsed_time * 1000
        idle_time_ms = idle_time * 1000

        self._telemetry_service.publish(
            event=event,
            loop_time_ms=loop_time_ms,
            idle_time_ms=idle_time_ms,
            cycle_index=None,
            cycle_ratio=None,
            leg_positions=None,
        )

    def _sleep_until_next_frame(self, idle_time: float) -> None:
        time.sleep(idle_time)
