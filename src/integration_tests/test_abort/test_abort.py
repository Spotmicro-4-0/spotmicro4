#!/home/pi/spotmicroai/venv/bin/python3 -u
"""
SpotMicroAI Abort Mechanism Test Utility (Safe Version)

This script safely tests the GPIO pin used by the abort controller (OE pin) to
enable or disable the PCA9685 servo driver board.

Safety guarantees:
- Starts with servos DISABLED (OE = HIGH → outputs off, servos limp)
- Clears PCA9685 channel outputs before enabling to avoid sudden motion
- Allows user-controlled enable/disable cycle with visible logs

Usage:
    python3 test_abort.py
"""

import time
import RPi.GPIO as GPIO
import busio
import board
from adafruit_pca9685 import PCA9685  # type: ignore

from spotmicroai.core.utilities.log import Logger
from spotmicroai.core.utilities.config import Config


def safe_clear_pca_outputs(pca_address: int, ref_clock: int, freq: int):
    """Initialize PCA9685 and clear all outputs to 0 duty."""
    i2c = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c, address=pca_address, reference_clock_speed=ref_clock)
    pca.frequency = freq

    for ch in range(16):
        pca.channels[ch].duty_cycle = 0  # zero each output

    pca.deinit()


def main():
    log = Logger().setup_logger("Test Abort (Safe)")
    log.info("Starting safe abort mechanism test...")

    config = Config()
    gpio_port = config.abort_controller.gpio_port

    # Read PCA configuration for clearing outputs
    pca = config.motion_controller.pca9685
    pca_address = int(pca.address, 0)
    ref_clock = pca.reference_clock_speed
    freq = pca.frequency

    log.info("Ensure your GPIO pin is connected to the OE port on the PCA9685 board.")
    log.info(f"Configured GPIO pin: {gpio_port}")
    log.info(f"PCA9685 address: {hex(pca_address)}, frequency: {freq} Hz")
    input("Press Enter to start the safe test...")

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    try:
        # --- SAFE STARTUP ---
        # 1. Keep OE HIGH (outputs disabled → servos limp)
        GPIO.setup(gpio_port, GPIO.OUT, initial=GPIO.HIGH)
        log.info("OE set HIGH → servos DISABLED (limp).")

        # 2. Clear PCA outputs to prevent sudden jumps on enable
        log.info("Clearing PCA9685 outputs...")
        safe_clear_pca_outputs(pca_address, ref_clock, freq)
        log.info("PCA outputs cleared (all channels 0 duty).")

        # 3. Wait for user to enable
        input("Press Enter to ENABLE outputs (OE LOW)...")

        GPIO.output(gpio_port, GPIO.LOW)
        log.info("OE set LOW → servos ENABLED.")
        log.info("Servos active for 5 seconds...")
        time.sleep(5)

        # 4. Re-disable outputs
        GPIO.output(gpio_port, GPIO.HIGH)
        log.info("OE set HIGH → servos DISABLED (limp again).")
        time.sleep(1)

        log.info("Test completed successfully.")
    except Exception as e:
        log.error(f"Abort test failed: {e}")
    finally:
        GPIO.output(gpio_port, GPIO.HIGH)
        GPIO.cleanup(gpio_port)
        log.info("GPIO cleaned up. OE HIGH, servos safe and limp.")


if __name__ == "__main__":
    main()
