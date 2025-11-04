#!/usr/bin/env python3

import multiprocessing
import sys
from time import sleep

from spotmicroai import labels
from spotmicroai.logger import Logger
from spotmicroai.runtime.abort_controller.abort_controller import AbortController
from spotmicroai.runtime.lcd_screen_controller.lcd_screen_controller import LCDScreenController
from spotmicroai.runtime.messaging import MessageBus
from spotmicroai.runtime.motion_controller.motion_controller import MotionController
from spotmicroai.runtime.remote_controller.remote_controller import RemoteControllerController
from spotmicroai.runtime.telemetry_controller.telemetry_controller import TelemetryController

log = Logger().setup_logger()


def process_controller(controller_class: type, message_bus: MessageBus) -> None:
    controller = controller_class(message_bus)
    controller.do_process_events_from_queues()


def main():
    message_bus = MessageBus()
    log.info(labels.MAIN_MESSAGE_BUS_CREATED)

    controller_types = [
        AbortController,
        MotionController,
        RemoteControllerController,
        LCDScreenController,
        TelemetryController,
    ]

    processes = []
    for controller_class in controller_types:
        process = multiprocessing.Process(target=process_controller, args=(controller_class, message_bus))
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
    log.info(labels.MAIN_STARTING)

    try:
        main()

    except KeyboardInterrupt:
        log.info(labels.MAIN_TERMINATED_CTRL_C)

    else:
        log.info(labels.MAIN_TERMINATED_NORMAL)
