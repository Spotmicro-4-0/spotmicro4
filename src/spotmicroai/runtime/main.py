#!/usr/bin/env python3

import argparse
import multiprocessing
import sys
from time import sleep

from spotmicroai import labels
from spotmicroai.logger import Logger
from spotmicroai.runtime.abort_controller.abort_controller import AbortController
from spotmicroai.runtime.lcd_screen_controller.lcd_screen_controller import LcdScreenController
from spotmicroai.runtime.messaging import MessageBus
from spotmicroai.runtime.motion_controller.motion_controller import MotionController
from spotmicroai.runtime.remote_controller.remote_controller import RemoteControllerController
from spotmicroai.runtime.telemetry_controller.telemetry_controller import TelemetryController

log = Logger().setup_logger()


def process_controller(controller_class: type) -> None:
    controller = controller_class()
    controller.do_process_events_from_queues()


def main(telemetry_enabled: bool = True):
    message_bus = MessageBus()
    log.info(labels.MAIN_MESSAGE_BUS_CREATED)

    controller_types = [
        AbortController,
        MotionController,
        RemoteControllerController,
        LcdScreenController,
    ]

    if telemetry_enabled:
        controller_types.append(TelemetryController)

    processes = []
    for controller_class in controller_types:
        process = multiprocessing.Process(target=process_controller, args=(controller_class,))
        process.daemon = True
        process.start()
        sleep(0.1)
        if not process.is_alive():
            log.error(labels.MAIN_ERROR_CONTROLLER_FAILED.format(controller_class.__name__))
            sys.exit(1)
        processes.append(process)

    for process in processes:
        process.join()

    message_bus.close()
    log.info(labels.MAIN_MESSAGE_BUS_CLOSING)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SpotmicroAI Runtime')
    parser.add_argument('--telemetry-off', action='store_true', help='Disable telemetry controller')
    args = parser.parse_args()

    log.info(labels.MAIN_STARTING)
    abort_ctrl = AbortController()

    try:
        main(telemetry_enabled=not args.telemetry_off)

    except KeyboardInterrupt:
        log.info(labels.MAIN_TERMINATED_CTRL_C)
        abort_ctrl.abort()

    else:
        log.info(labels.MAIN_TERMINATED_NORMAL)
        abort_ctrl.abort()
