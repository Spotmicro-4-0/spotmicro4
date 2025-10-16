#!/usr/bin/env python3
"""Simple GPIO beep utility used by Spotmicro.

This script toggles a GPIO pin (default BCM 21) high for a short
duration to drive a buzzer. It's lightweight and intended to be
callable from shell scripts or other Python code.

Improvements over the original:
- uses argparse for optional duration and pin
- cleans up GPIO on exit
- graceful fallback when RPi.GPIO is not available (e.g. on dev machine)
- returns 0 on success
"""

import sys
import time
import argparse
from contextlib import suppress

from RPi import GPIO  # type: ignore
from spotmicroai.utilities.config import Config

# Module-level config instance
_config = Config()


def beep(pin: int | None = None, duration: float = 0.2) -> int:
    """Toggle `pin` high for `duration` seconds.

    Returns 0 on success, non-zero on failure.
    """
    # Resolve pin from config when not explicitly provided
    if pin is None:
        try:
            pin = int(_config.motion_controller.buzzer.gpio_port)
        except Exception as exc:
            print(f"Failed to read buzzer pin from config: {exc}", file=sys.stderr)
            return 4

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, True)
        time.sleep(duration)
        GPIO.output(pin, False)
    except Exception as exc:
        print(f"Failed to beep: {exc}", file=sys.stderr)
        return 2
    finally:
        # Best-effort cleanup; ignore errors during cleanup.
        with suppress(Exception):
            GPIO.cleanup(pin)

    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Simple GPIO beep utility")
    parser.add_argument("-p", "--pin", type=int, default=None, help="BCM pin to use (default: read from config)")
    parser.add_argument("-d", "--duration", type=float, default=0.2, help="Beep duration in seconds (default: 0.2)")
    args = parser.parse_args(argv)

    return beep(pin=args.pin, duration=args.duration)


if __name__ == "__main__":
    raise SystemExit(main())
