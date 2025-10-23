#!/home/pi/spotmicroai/venv/bin/python3 -u
"""
SpotMicroAI LCD Screen Test Utility

This script runs a series of tests on the I²C-connected 16x2 LCD screen used by SpotMicroAI.
It verifies:
    - Backlight functionality
    - Display of characters and strings
    - Custom character loading
    - Character animation and movement
    - Full-screen fill tests

The I²C address is read from the main configuration file (`~/spotmicroai.json`).
Use `i2cdetect -y 1` to verify your device’s I²C address before running this test.

Usage:
    python3 test_lcd_screen.py
"""

import time

from spotmicroai.configuration import ConfigProvider
from spotmicroai.drivers.lcd_16x2 import Lcd16x2
from spotmicroai.logger import Logger

# ------------------------------------------------------------------------------------------
# Test Functions
# ------------------------------------------------------------------------------------------


def test_backlight(lcd, log):
    """Test 0: Toggle LCD backlight on and off."""
    log.info("Running Test 0 - Backlight Toggle")
    lcd.lcd_clear()
    lcd.backlight(0)
    time.sleep(1)
    lcd.backlight(1)
    time.sleep(1)


def test_full_lines(lcd, log):
    """Test 1: Display full-width strings on both lines."""
    log.info("Running Test 1 - Full Line Display")
    lcd.lcd_clear()
    lcd.lcd_display_string("1234567890123456", 1)
    lcd.lcd_display_string("ABCDEFGHIJKLMNOP", 2)
    time.sleep(2)


def test_custom_chars_scroll(lcd, log):
    """Test 2: Load custom characters and scroll them across the screen."""
    log.info("Running Test 2 - Custom Characters Scroll")

    fontdata = [
        [0x00, 0x00, 0x03, 0x04, 0x08, 0x19, 0x11, 0x10],
        [0x00, 0x1F, 0x00, 0x00, 0x00, 0x11, 0x11, 0x00],
        [0x00, 0x00, 0x18, 0x04, 0x02, 0x13, 0x11, 0x01],
        [0x12, 0x13, 0x1B, 0x09, 0x04, 0x03, 0x00, 0x00],
        [0x00, 0x11, 0x1F, 0x1F, 0x0E, 0x00, 0x1F, 0x00],
        [0x09, 0x19, 0x1B, 0x12, 0x04, 0x18, 0x00, 0x00],
        [0x1F, 0x00, 0x04, 0x0E, 0x00, 0x1F, 0x1F, 0x1F],
    ]

    lcd.lcd_clear()
    lcd.lcd_load_custom_chars(fontdata)

    # Write first set of characters to both rows
    lcd.lcd_write(0x80)
    for i in range(3):
        lcd.lcd_write_char(i)
    lcd.lcd_write(0xC0)
    for i in range(3, 6):
        lcd.lcd_write_char(i)

    time.sleep(1)

    # Animate movement
    for x in range(0, 14):
        lcd.lcd_clear()
        for row_offset, char_offset in enumerate((0, 3)):
            lcd.lcd_display_string_pos(chr(char_offset), row_offset + 1, x)
            lcd.lcd_display_string_pos(chr(char_offset + 1), row_offset + 1, x + 1)
            lcd.lcd_display_string_pos(chr(char_offset + 2), row_offset + 1, x + 2)
        time.sleep(0.5)


def test_positioned_text(lcd, log):
    """Test 3: Display text in specific positions."""
    log.info("Running Test 3 - Positioned Text")
    lcd.lcd_clear()
    lcd.lcd_display_string_pos("Testing", 1, 1)
    time.sleep(1)
    lcd.lcd_display_string_pos("Testing", 2, 3)
    time.sleep(1)


def test_progress_bar(lcd, log):
    """Test 4: Animate a simple left-to-right bar fill."""
    log.info("Running Test 4 - Progress Bar Animation")

    fontdata = [
        [0x01, 0x03, 0x07, 0x0F, 0x0F, 0x07, 0x03, 0x01],
        [0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10],
        [0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18],
        [0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C],
        [0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E],
        [0x00, 0x01, 0x03, 0x07, 0x0F, 0x1F, 0x1F, 0x1F],
    ]

    lcd.lcd_clear()
    lcd.lcd_load_custom_chars(fontdata)

    block = chr(255)  # solid block
    for pos in range(16):
        for char_code in range(1, 5):
            lcd.lcd_display_string_pos(chr(char_code), 1, pos)
            lcd.lcd_display_string_pos(chr(char_code), 2, pos)
            time.sleep(0.1)
        lcd.lcd_display_string_pos(block, 1, pos)
        lcd.lcd_display_string_pos(block, 2, pos)
        time.sleep(0.1)


def test_full_blocks(lcd, log):
    """Test 5: Fill both lines completely with solid blocks."""
    log.info("Running Test 5 - Full Block Fill")
    block = chr(255)
    lcd.lcd_clear()
    lcd.lcd_display_string(block * 16, 1)
    lcd.lcd_display_string(block * 16, 2)
    time.sleep(1)


# ------------------------------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------------------------------


def main():
    """Initialize and execute all LCD test sequences."""
    log = Logger().setup_logger("LCD Screen Test")
    log.info("Starting LCD Screen Test Suite...")

    config_provider = ConfigProvider()
    i2c_address = int(config_provider.lcd_screen_controller.address, 0)

    log.info('Use "i2cdetect -y 1" to list connected I2C devices.')
    log.info(f"Configured LCD address: {hex(i2c_address)}")

    input("Press Enter to start the tests...")

    lcd = Lcd16x2(address=i2c_address)

    try:
        test_backlight(lcd, log)
        test_full_lines(lcd, log)
        test_custom_chars_scroll(lcd, log)
        test_positioned_text(lcd, log)
        test_progress_bar(lcd, log)
        test_full_blocks(lcd, log)
        log.info("All LCD tests completed successfully.")
    except Exception as e:
        log.error(f"LCD test failed: {e}")
    finally:
        lcd.lcd_clear()
        lcd.backlight(0)
        log.info("LCD cleared and backlight turned off.")


if __name__ == "__main__":
    main()
