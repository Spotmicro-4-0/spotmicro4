#!/home/pi/spotmicroai/venv/bin/python3 -u
"""
Buzzer Test Utility for SpotMicroAI.

This script allows interactive testing of the robot's buzzer using the terminal.
It presents a simple menu with multiple beep patterns (short, long, multiple)
using the `pick` library for selection.

The script reads the GPIO pin configuration from the SpotMicroAI Config service
and toggles the buzzer accordingly.

Usage:
    python3 buzzer_test.py
"""

import sys
import time
import RPi.GPIO as GPIO
from pick import pick

from spotmicroai.core.utilities.log import Logger
from spotmicroai.core.utilities.config import Config


def beep(gpio_port: int, duration: float, count: int = 1, delay: float = 0.5) -> None:
    """
    Activate the buzzer on the specified GPIO port for a given duration.

    Args:
        gpio_port (int): The GPIO pin number used for the buzzer.
        duration (float): Duration of each beep in seconds.
        count (int): Number of times to repeat the beep pattern.
        delay (float): Delay between consecutive beeps.
    """
    for _ in range(count):
        GPIO.output(gpio_port, True)
        time.sleep(duration)
        GPIO.output(gpio_port, False)
        if count > 1:
            time.sleep(delay)


def main() -> None:
    """
    Main entry point for the buzzer test program.

    Presents a simple interactive menu to select a buzzer test pattern.
    Cleans up GPIO state upon exit.
    """
    log = Logger().setup_logger("Buzzer Test")
    log.info("Initializing Buzzer Test...")

    config = Config()
    gpio_port = config.motion_controller.buzzer.gpio_port

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpio_port, GPIO.OUT, initial=GPIO.LOW)

    options = ["Short Beep", "Long Beep", "Multiple Beeps", "Exit"]
    title = "Select the pattern you want to test"

    try:
        while True:
            selected_option, _ = pick(options, title)

            if selected_option == "Short Beep":
                beep(gpio_port, duration=1.0)
            elif selected_option == "Long Beep":
                beep(gpio_port, duration=3.0)
            elif selected_option == "Multiple Beeps":
                beep(gpio_port, duration=0.8, count=3, delay=0.5)
            else:
                log.info("Exiting buzzer test.")
                break
    finally:
        GPIO.output(gpio_port, False)
        GPIO.cleanup(gpio_port)
        log.info("GPIO cleaned up successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
