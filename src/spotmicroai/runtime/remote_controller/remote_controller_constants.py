"""
Remote controller configuration constants.

These constants define the behavior of the joystick/remote controller input handling,
including timing, filtering, and device reconnection parameters.
"""

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
# Values smaller than this threshold are treated as 0.0
DEADZONE = 0.08

# Minimum absolute change in axis value required before updating state.
# Prevents noisy readings from triggering unnecessary updates.
AXIS_UPDATE_THRESHOLD = 0.01

# ===============================
# Reconnection and Device Search
# ===============================
# Delay between joystick access retries when device is not yet ready or permissions unavailable (in seconds).
RECONNECT_RETRY_DELAY = 2.0

# Delay between failed device detection cycles (in seconds).
DEVICE_SEARCH_INTERVAL = 2.5

# ===============================
# Joystick Input Buffer
# ===============================
# Size of the joystick event buffer to read from /dev/input (in bytes)
JSDEV_READ_SIZE = 8
