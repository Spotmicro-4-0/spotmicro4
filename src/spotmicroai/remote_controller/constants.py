"""
constants.py
-------------
Central location for all tunable parameters used by the RemoteControllerController.
Modify these values to adjust responsiveness, safety, and filtering behavior
without touching the main control logic.
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
