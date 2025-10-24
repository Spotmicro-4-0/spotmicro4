"""
Localization strings for MenuApp.

This module contains all user-facing strings used in the menu system.
Centralizing them here makes it easier to support multiple languages in the future.
"""

# Error messages for terminal size
MSG_TERMINAL_TOO_SMALL = "Terminal too small!"
MSG_RESIZE_CONTINUE = "Please resize to continue"
MSG_HEIGHT_TOO_SMALL = "Terminal height too small"

# Help text
MSG_HELP_TEXT = "Use ↑ ↓ to navigate, ENTER to select and q/ESC to quit"

# Error messages for actions
MSG_INVALID_ACTION = "Invalid action: {}"
MSG_INVALID_SUBMENU_TARGET = "Invalid or missing submenu target."
MSG_SUBMENU_NOT_FOUND = "Submenu '{}' not found."
MSG_MISSING_COMMAND = "Missing 'command' field for action 'run'"

# Command execution messages
MSG_RUNNING_COMMAND = "[INFO] Running: {}"
MSG_COMMAND_FAILED = "[ERROR] Command failed with exit code {}"
MSG_PRESS_ENTER_RETURN = "Press Enter to return to menu..."

# General error messages
MSG_ERROR_PREFIX = "[ERROR] {}"
MSG_PRESS_ENTER_CONTINUE = "Press Enter to continue..."

# Calibration UI strings
CAL_TITLE = "=== Servo Calibration Menu ==="
CAL_INSTRUCTION = "Use ↑ ↓ to select, ENTER to set angle, q/ESC to quit"
CAL_EXIT_LABEL = "Exit"
CAL_EXIT_SHORTCUT = "q"
CAL_SERVO_ADJUST_INSTRUCTION = "↑/↓ adjust ±{:.0f}°. ENTER moves. b/ESC exits."
CAL_SERVO_DISPLAY = "{}: {:.1f}° [{:.0f}µs]"
CAL_INPUT_PROMPT = "Input: "
CAL_STATUS_REAPPLIED = "Reapplied {} to {:.1f}°"
CAL_STATUS_MOVED = "Moved {} to {:.1f}°"
CAL_STATUS_INVALID_ANGLE = "Invalid angle. Use a numeric value."
CAL_STATUS_RETURNING = "Returning to menu."
CAL_STATUS_UNSUPPORTED_KEY = "Unsupported key. Use digits, ENTER, arrows, or b/ESC."

# Calibration Wizard strings
WIZARD_TITLE = "Calibration Wizard - {}"
WIZARD_JOINT_TYPE_LINE = "Joint Type: {}"
WIZARD_INSTRUCTION_1 = "You will be guided through physical calibration."
WIZARD_INSTRUCTION_2 = "Follow the on-screen instructions to position"
WIZARD_INSTRUCTION_3 = "the joint at specific angles."
WIZARD_INSTRUCTION_4 = "The servo will move as you adjust it."
WIZARD_INSTRUCTION_5 = "Use arrow keys to fine-tune the position."
WIZARD_PRESS_ENTER_BEGIN = "Press ENTER to begin"
WIZARD_PRESS_ESC_CANCEL = "Press ESC to cancel"
WIZARD_POINT_TITLE = "Point {}/{}"
WIZARD_EXPECTED_ANGLE = "Expected angle: {}°"
WIZARD_CURRENT_PULSE = "Current Pulse: {} µs"
WIZARD_MIN_PULSE_LABEL = "Min Pulse: {}"
WIZARD_MAX_PULSE_LABEL = "Max Pulse: {}"
WIZARD_DASH = "--"
WIZARD_ADJUST_INSTRUCTION = "↑/↓ adjust ±{} µs"
WIZARD_ENTER_CONFIRM_ESC_CANCEL = "ENTER to confirm, ESC to cancel"
WIZARD_SUMMARY_TITLE = "Calibration Summary"
WIZARD_POINT_SUMMARY = "Point {}: {} µs @ {}°"
WIZARD_TARGET_RANGE = "Target Range: {}° to {}°"
WIZARD_REST_ANGLE = "Rest Angle: {}°"
WIZARD_ENTER_SAVE_ESC_CANCEL = "ENTER to save, ESC to cancel"
WIZARD_ERROR_CALIBRATION = "Error during calibration: {}"
WIZARD_NEED_TWO_POINTS = "Need at least 2 calibration points"
WIZARD_PULSE_NOT_CAPTURED_1 = "Pulse width not captured for point 1"
WIZARD_PULSE_NOT_CAPTURED_2 = "Pulse width not captured for point 2"
WIZARD_INVALID_SERVO_ID = "Error: Invalid servo ID '{}'"
WIZARD_VALID_SERVO_IDS = "Valid servo IDs: {}"
WIZARD_ERROR_CALIBRATING = "\n✗ Error calibrating {}: {}"
WIZARD_SEPARATOR = "=" * 50
WIZARD_SUCCESS_COUNT = "\n✓ Successfully calibrated: {} servos"
WIZARD_FAILED_COUNT = "\n✗ Failed: {} servos"
WIZARD_FAILED_SERVOS = "\nFailed servos: {}"
WIZARD_INTERRUPTED = "\n✗ Calibration interrupted by user"
WIZARD_ERROR_GENERAL = "\n✗ Error during calibration: {}"
WIZARD_SUCCESS_SINGLE = "\n✓ Successfully calibrated {}"
WIZARD_CANCELLED = "\n✗ Calibration cancelled for {}"
WIZARD_USAGE = "Usage: calibration_wizard.py <SERVO_ID>"
WIZARD_USAGE_ALL = "       calibration_wizard.py all (to calibrate all servos sequentially)"
WIZARD_JOINT_TYPE_ERROR = "Could not determine joint type for servo: {}"
