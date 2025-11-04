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
WIZARD_INFERRED_MIN_PULSE = "Inferred Min Pulse ({}°): {} µs"
WIZARD_INFERRED_MAX_PULSE = "Inferred Max Pulse ({}°): {} µs"
WIZARD_ERROR_REST_ANGLE_OUT_OF_RANGE = (
    "Rest angle {:.1f}° is outside the target range [{:.1f}°, {:.1f}°]. "
    "Please adjust the rest_angle in calibration specs."
)
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

# Manual Servo Control strings
MANUAL_TITLE = "Manual Servo Control - {}"
MANUAL_CURRENT_PULSE_WIDTH = "Current Pulse Width:"
MANUAL_SERVO_RANGE = "Servo Range:"
MANUAL_REST_ANGLE = "Rest Angle:"
MANUAL_ADJUST_INSTRUCTION = "↑/↓ adjust ±{}°"
MANUAL_EXIT_INSTRUCTION = "ESC to exit"
MANUAL_INVALID_SERVO_ID = "Error: Invalid servo ID '{}'"
MANUAL_VALID_SERVO_IDS = "Valid servo IDs: {}"
MANUAL_COMPLETED = "\n✓ Manual control completed for {}"
MANUAL_CANCELLED = "\n✗ Manual control cancelled for {}"
MANUAL_INTERRUPTED = "\n✗ Manual control interrupted by user"
MANUAL_ERROR = "\n✗ Error during manual control: {}"
MANUAL_USAGE = "Usage: servo_manual_control.py <SERVO_ID>"

# Diagnostics strings
DIAG_TITLE = "Servo Diagnostics"
DIAG_INSTRUCTION = "Test servo symmetry and range of motion"
DIAG_JOINT_TYPE_LABEL = "Testing: {}"
DIAG_STEP_TITLE = "Step {}/{}"
DIAG_MOVING_TO_REST = "Moving servos to rest position..."
DIAG_MOVING_TO_MIN = "Moving to MIN position..."
DIAG_MOVING_TO_MAX = "Moving to MAX position..."
DIAG_MOVING_TO_REST_FINAL = "Returning to rest position..."
DIAG_SWEEP_PROGRESS = "Sweep: {:.0f}° → {:.0f}° ({:.0f}%)"
DIAG_PRESS_ENTER_NEXT = "Press ENTER to continue to next step"
DIAG_PRESS_ESC_CANCEL = "Press ESC to cancel diagnostics"
DIAG_ENTER_BEGIN = "Press ENTER to begin diagnostics"
DIAG_CURRENT_ANGLES = "Current Angles:"
DIAG_SERVO_ANGLE_DISPLAY = "  {}: {:.0f}°"
DIAG_TEST_COMPLETE = "Diagnostics Complete!"
DIAG_SUMMARY = "All servo sweeps completed successfully."
DIAG_PRESS_ENTER_FINISH = "Press ENTER to finish"
DIAG_INTERRUPTED = "\n✗ Diagnostics interrupted by user"
DIAG_ERROR_GENERAL = "\n✗ Error during diagnostics: {}"
DIAG_USAGE = "Usage: diagnostics.py"
DIAG_SERVO_ERROR = "Error moving servo {}: {}"
DIAG_SWEEP_STEP_FAILED = "Error during sweep: {}"
DIAG_INTRO_LINE_1 = "Sweep all servos to verify proper operation."
DIAG_INTRO_LINE_2 = "Each joint type tested sequentially:"
DIAG_INTRO_LINE_3 = "Shoulders → Legs → Feet"
DIAG_INTRO_LINE_5 = "Observe servos for:"
DIAG_INTRO_LINE_6 = "  • Smooth motion"
DIAG_INTRO_LINE_7 = "  • Left/right symmetry"
DIAG_INTRO_LINE_8 = "  • Full range of motion"
DIAG_SUCCESS_ALL_SERVOS = "✓ All servo groups tested successfully"
DIAG_SUCCESS_NO_ERRORS = "✓ No errors detected during diagnostics"

# Calibration Wizard String Constants
# String formatting templates and constants
CALIBRATION_POINT_DISPLAY_FORMAT = "{} µs @ {}°"
CALIBRATION_POINT_LABEL_PREFIX = "Point {}: "
UNDERSCORE_CHAR = "_"
SPACE_CHAR = " "

# Error messages for servo configuration validation
ERR_SERVO_CONFIG_MIN_MAX_EQUAL = (
    "Invalid servo config for {servo_name}: min_pulse ({min_pulse}) cannot equal max_pulse ({max_pulse})"
)
ERR_SERVO_CONFIG_MIN_PULSE_OUT_OF_RANGE = "Invalid servo config for {servo_name}: min_pulse ({min_pulse}) must be between {SERVO_PULSE_WIDTH_MIN} and {SERVO_PULSE_WIDTH_MAX} microseconds"
ERR_SERVO_CONFIG_MAX_PULSE_OUT_OF_RANGE = "Invalid servo config for {servo_name}: max_pulse ({max_pulse}) must be between {SERVO_PULSE_WIDTH_MIN} and {SERVO_PULSE_WIDTH_MAX} microseconds"

# System Controller Messages
# Abort Controller
ABORT_STARTING_CONTROLLER = 'Starting controller...'
ABORT_ATTEMPTING_GPIO = 'Attempting to configure GPIO pins'
ABORT_GPIO_SUCCESS = 'GPIO pins configured successfully.'
ABORT_GPIO_WARNING = 'GPIO pins may not be fully configured, but proceeding anyway.'
ABORT_GPIO_ERROR = 'Unable to access GPIO pins to configure the abort controller.'
ABORT_INIT_ERROR = 'Abort controller initialization problem'
ABORT_TERMINATED = 'Terminated'
ABORT_QUEUE_ERROR = 'Unknown problem while processing the queue of the abort controller'

# Motion Controller
MOTION_INIT_PROBLEM = 'Motion controller initialization problem'
MOTION_GRACEFUL_SHUTDOWN = "Graceful shutdown initiated..."
MOTION_PCA_DEACTIVATE_WARNING = "Could not deactivate PCA9685 cleanly: {}"
MOTION_TERMINATED = "Motion controller terminated safely."
MOTION_INACTIVITY_WARNING = 'Inactivity lasted {} seconds. Press start to reactivate'
MOTION_SHUTDOWN_SERVOS = 'Shutting down the servos.'
MOTION_PRESS_START_ENABLE = 'Press START/OPTIONS to enable the servos'
MOTION_TELEMETRY_QUEUE_FULL = "Telemetry queue full, dropping oldest frame"
MOTION_TELEMETRY_UNAVAILABLE = "Telemetry queue not available; telemetry data dropped"
MOTION_TELEMETRY_ERROR = "Telemetry dispatch error: {}"
MOTION_REACTIVATE_SERVOS = 'Press START/OPTIONS to re-enable the servos'

# Main Runtime
MAIN_MESSAGE_BUS_CREATED = 'Created the message bus'
MAIN_MESSAGE_BUS_CLOSING = 'Closing the message bus'
MAIN_ERROR_CONTROLLER_FAILED = "SpotmicroAI can't work without {}"
MAIN_STARTING = 'Spotmicro starting...'
MAIN_TERMINATED_CTRL_C = 'Terminated due Control+C was pressed'
MAIN_TERMINATED_NORMAL = 'Normal termination'

# LCD Screen Controller
LCD_STARTING_CONTROLLER = 'Starting controller...'
LCD_INIT_ERROR = 'LCD Screen controller initialization problem, module not critical, skipping: {}'
LCD_TERMINATED = 'Terminated'
LCD_WORKING_WITHOUT = "SpotMicro is working without LCD Screen"
LCD_QUEUE_ERROR = 'Unknown problem while processing the queue of the lcd screen controller: {}'
LCD_TEMP_ERROR = 'Error reading system temperature: {}'

# Remote Controller
REMOTE_STARTING_CONTROLLER = 'Starting controller...'
REMOTE_INIT_ERROR = 'Remote controller controller initialization problem: {}'
REMOTE_TERMINATED = 'Terminated'
REMOTE_QUEUE_ERROR = 'Unknown problem while processing the queue of the remote controller: {}'

# Remote Control Service
REMOTE_LOOKING_FOR_DEVICES = 'Looking for connected devices: {}'
REMOTE_ATTEMPTING_OPEN = 'Attempting to open {}...'
REMOTE_OPEN_SUCCESS = '{} opened successfully.'
REMOTE_OPEN_WARNING = 'Could not open {} with non-blocking I/O, falling back to blocking: {}'
REMOTE_INIT_MAPPING_ERROR = 'Failed to initialize device mappings: {}'
REMOTE_CONNECTED_TO = 'Connected to device: {}'
REMOTE_AXES_FOUND = '{} axes found: {}'
REMOTE_BUTTONS_FOUND = '{} buttons found: {}'
REMOTE_READ_ERROR = 'Error reading joystick events: {}'
REMOTE_CLOSE_WARNING = 'Error closing device: {}'

# Telemetry Controller
TELEMETRY_INITIALIZED = 'Telemetry controller initialized'
TELEMETRY_INIT_ERROR = 'Telemetry controller initialization problem, module not critical, skipping: {}'
TELEMETRY_TERMINATED = 'Telemetry controller terminated'
TELEMETRY_NOT_ALIVE = 'Telemetry controller is not alive, skipping processing loop'
TELEMETRY_UNEXPECTED_TYPE = 'Telemetry controller received unexpected payload type: {}'
TELEMETRY_QUEUE_ERROR = 'Unexpected telemetry queue error: {}'
TELEMETRY_RENDER_ERROR = 'Telemetry rendering error: {}'
TELEMETRY_DISPLAY_TITLE = 'SpotMicroAI Telemetry'
TELEMETRY_DISPLAY_TIMESTAMP = 'Timestamp: {}'
TELEMETRY_SYSTEM_STATUS = 'System Status'
TELEMETRY_MOTION_PARAMS = 'Motion Parameters'
TELEMETRY_CONTROLLER_INPUT = 'Controller Input'
TELEMETRY_LEG_COORDS = 'Leg Coordinates'
TELEMETRY_SERVO_ANGLES = 'Servo Angles'
TELEMETRY_FOOTER = 'Press START to disable servos | Press CTRL+C to exit'
TELEMETRY_RESIZE_MSG = 'Resize terminal to at least {}x{} for telemetry.'

# Configuration Provider
CONFIG_LOADING = 'Loading configuration...'
CONFIG_LOAD_ERROR = 'Problem while loading the configuration file: {}'
CONFIG_LOADED_FROM = 'Configuration loaded from {}'
CONFIG_NOT_EXIST = "Configuration file doesn't exist, aborting."
CONFIG_INVALID_JSON = "Configuration file is not valid JSON: {}"
CONFIG_ERROR = "Problem loading configuration: {}"
CONFIG_SAVED = 'Configuration saved to {}'
CONFIG_SAVE_ERROR = "Problem saving the configuration file: {}"
CONFIG_SERVO_NOT_FOUND = "Servo '{}' not found in configuration"
CONFIG_SERVO_MISSING = "Servo '{}' not found"
CONFIG_POSE_NOT_FOUND = "Pose '{}' not found in configuration"

# Coordinate/Kinematics
IK_FALLBACK_WARNING = "IK fallback due to {} for ({})"
IK_ERROR_LOG = "IK error for {}: {}"

# Diagnostics
DIAG_COMPLETED_SUCCESSFULLY = "✓ Diagnostics completed successfully"
