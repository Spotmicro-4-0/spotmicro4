### Inverse Kinematics Constants ###
# Constants for inverse kinematics calculations (in mm)
LEG_LENGTH = 110
FOOT_LENGTH = 138
SHOULDER_LENGTH = 57
SAFE_NEUTRAL = (0.0, 0.0, 0.0)

### Motion Controller Constants ###
# Motion controller constants
# LEG_SERVO_OFFSET = 120
# FOOT_SERVO_OFFSET = 0
ROTATION_OFFSET = 40
INACTIVITY_TIME = 10

# Walking speed
MAX_WALKING_SPEED = 15

# Lean and height multipliers
LEAN_MULTIPLIER = 50
HEIGHT_MULTIPLIER = 40

# Rotation increment
ROTATION_INCREMENT = 0.025

# Buzzer
BEEP_DURATION = 0.5

# Debounce Button
DEFAULT_DEBOUNCE_TIME = 0.5

FRAME_RATE_HZ = 50
FRAME_DURATION = 1.0 / FRAME_RATE_HZ
TELEMETRY_UPDATE_INTERVAL = 2  # Update telemetry display every N frames

# Diagnostics Constants
SWEEP_RATE_DEG_PER_FRAME = 0.5  # Configurable sweep rate: degrees per frame (adjust for speed)

DEFAULT_SLEEP = 0.1


# Controller Constants
# ===============================
# General Timing and Publishing
# ===============================
# Rate (in Hz) at which the current joystick state is broadcast to the motion queue.
PUBLISH_RATE_HZ = 20.0
# Delay between read loop iterations (in seconds)
READ_LOOP_SLEEP = 0.005
# ===============================
# Analog Input Filtering
# ===============================
# Deadzone threshold for analog stick drift (0.0–1.0).
DEADZONE = 0.08
# Minimum absolute change in axis value required before updating state.
AXIS_UPDATE_THRESHOLD = 0.01
# ===============================
# Reconnection and Device Search
# ===============================
# Delay between joystick access retries when device is not yet ready or permissions unavailable.
RECONNECT_RETRY_DELAY = 2.0
# Delay between failed device detection cycles.
DEVICE_SEARCH_INTERVAL = 2.5

# ===============================
# Calibration Wizard Constants
# ===============================
POPUP_HEIGHT = 16
POPUP_WIDTH = 75
CALIBRATION_STEP_SIZE = 10  # microseconds or degrees
# Offset in degrees for servo calibration due to geometry
GEOMETRY_OFFSET_SHOULDER = 0
GEOMETRY_OFFSET_LEG = 9.5
GEOMETRY_OFFSET_FOOT = 0

# ===============================
# Servo Validation Constants
# ===============================
SERVO_PULSE_WIDTH_MIN = 500  # microseconds
SERVO_PULSE_WIDTH_MAX = 2500  # microseconds

# ===============================
# Servo Manual Control Constants
# ===============================
ANGLE_STEP_SIZE = 1  # degrees per adjustment

# ===============================
# Remote Controller Constants
# ===============================
# Size of the joystick event buffer to read from /dev/input (in bytes)
JSDEV_READ_SIZE = 8

# ===============================
# Control Parameters
# ===============================
# Transition state filter time constant (seconds)
TRANSIT_TAU = 0.3
# Body motion rate limit (m/s) during transition state
TRANSIT_RL = 0.06
# Body motion angular rate limit (rad/s) during transition state
TRANSIT_ANGLE_RL = 0.35
# Maximum forward velocity (m/s)
MAX_FWD_VELOCITY = 0.4
# Maximum side velocity (m/s)
MAX_SIDE_VELOCITY = 0.4
# Maximum yaw rate (rad/s)
MAX_YAW_RATE = 0.35
# Loop time of main loop, seconds (0.02 s is 50 hz)
DT = 0.02

# ===============================
# Robot Wireframe Size Parameters
# ===============================
# Lengths representing a wireframe model of the robot. All lengths joint to joint
HIP_LINK_LENGTH = 0.055  # Straight line distance of the hip link (horizontal leg link)
UPPER_LEG_LINK_LENGTH = 0.1075  # Straight line distance of the upper leg link, joint to joint
LOWER_LEG_LINK_LENGTH = 0.130  # Straight line distance of the lower leg link, joint to joint
BODY_WIDTH = 0.078  # Horizontal width between hip joints
BODY_LENGTH = 0.186  # Length between shoulder joints

# ===============================
# Stance Parameters
# ===============================
DEFAULT_STAND_HEIGHT = 0.155  # Height of robot body center when standing
STAND_FRONT_X_OFFSET = 0.015  # Fwd/back offset of front two legs from default stance
STAND_BACK_X_OFFSET = -0.000  # Fwd/back offset of back two legs from default stance
# STAND_FRONT_X_OFFSET = -0.010  # Offset better tuned for trot gait
# STAND_BACK_X_OFFSET = -0.010  # Offset better tuned for trot gait
LIE_DOWN_HEIGHT = 0.083  # Height of body center when sitting
LIE_DOWN_FOOT_X_OFFSET = 0.065  # Fwd/back offset of all(?) feet from default stance when sitting
