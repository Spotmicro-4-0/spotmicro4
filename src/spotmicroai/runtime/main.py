#!/usr/bin/env python3

import multiprocessing
import sys

from spotmicroai.logger import Logger
from spotmicroai.runtime.abort_controller.abort_controller import AbortController
from spotmicroai.runtime.gait_controller.gait_controller import GaitController
from spotmicroai.runtime.lcd_screen_controller.lcd_screen_controller import LCDScreenController
from spotmicroai.runtime.motion_controller.motion_controller import MotionController
from spotmicroai.runtime.remote_controller.remote_controller import RemoteControllerController
from spotmicroai.runtime.telemetry_controller.telemetry_controller import TelemetryController

log = Logger().setup_logger()


def process_abort_controller(communication_queues):
    abort = AbortController(communication_queues)
    abort.do_process_events_from_queue()


def process_motion_controller(communication_queues):
    motion = MotionController(communication_queues)
    motion.do_process_events_from_queues()


def process_gait_controller(communication_queues):
    gait = GaitController(communication_queues)
    gait.do_process_events_from_queue()


def process_remote_controller_controller(communication_queues):
    remote_controller = RemoteControllerController(communication_queues)
    remote_controller.do_process_events_from_queues()


def process_output_lcd_screen_controller(communication_queues):
    lcd_screen = LCDScreenController(communication_queues)
    lcd_screen.do_process_events_from_queue()


def process_telemetry_controller(communication_queues):
    telemetry = TelemetryController(communication_queues)
    telemetry.do_process_events_from_queue()


def create_controllers_queues():
    communication_queues = {
        'abort_controller': multiprocessing.Queue(10),
        'motion_controller': multiprocessing.Queue(1),
        'gait_controller': multiprocessing.Queue(10),
        'lcd_screen_controller': multiprocessing.Queue(10),
        'telemetry_controller': multiprocessing.Queue(10),
    }

    log.info('Created the communication queues: %s', ", ".join(communication_queues.keys()))

    return communication_queues


def close_controllers_queues(communication_queues):
    log.info('Closing controller queues')

    for queue in communication_queues.items():
        queue.close()
        queue.join_thread()


def main():
    communication_queues = create_controllers_queues()

    # Abort controller
    # Controls the 0E port from PCA9685 to cut the power to the servos conveniently if needed.
    abort_controller = multiprocessing.Process(target=process_abort_controller, args=(communication_queues,))
    abort_controller.daemon = True  # The daemon dies if the parent process dies

    # Start the motion controller
    # Moves the servos
    motion_controller = multiprocessing.Process(target=process_motion_controller, args=(communication_queues,))
    motion_controller.daemon = True

    # Gait controller
    # Computes walking cycles at fixed frequency
    gait_controller = multiprocessing.Process(target=process_gait_controller, args=(communication_queues,))
    gait_controller.daemon = True

    # Activate Bluetooth controller
    # Let you move the dog using the bluetooth paired device
    remote_controller_controller = multiprocessing.Process(
        target=process_remote_controller_controller, args=(communication_queues,)
    )
    remote_controller_controller.daemon = True

    # Screen
    # Show status of the components in the screen
    lcd_screen_controller = multiprocessing.Process(
        target=process_output_lcd_screen_controller, args=(communication_queues,)
    )
    lcd_screen_controller.daemon = True

    # Telemetry controller
    # Renders system telemetry data on the host terminal
    telemetry_controller = multiprocessing.Process(target=process_telemetry_controller, args=(communication_queues,))
    telemetry_controller.daemon = True

    # Start the threads, queues messages are produced and consumed in those
    abort_controller.start()
    motion_controller.start()
    gait_controller.start()
    remote_controller_controller.start()
    lcd_screen_controller.start()
    telemetry_controller.start()

    if not abort_controller.is_alive():
        log.error("SpotMicro can't work without abort_controller")
        sys.exit(1)

    if not motion_controller.is_alive():
        log.error("SpotMicro can't work without motion_controller")
        sys.exit(1)

    if not gait_controller.is_alive():
        log.error("SpotMicro can't work without gait_controller")
        sys.exit(1)

    if not remote_controller_controller:
        log.error("SpotMicro can't work without remote_controller_controller")
        sys.exit(1)

    if not telemetry_controller.is_alive():
        log.error("SpotMicro can't work without telemetry_controller")
        sys.exit(1)

    # Make sure the thread/process ends
    abort_controller.join()
    motion_controller.join()
    gait_controller.join()
    remote_controller_controller.join()
    lcd_screen_controller.join()
    telemetry_controller.join()

    close_controllers_queues(communication_queues)


if __name__ == '__main__':
    log.info('Spotmicro starting...')

    try:
        main()

    except KeyboardInterrupt:
        log.info('Terminated due Control+C was pressed')

    else:
        log.info('Normal termination')
