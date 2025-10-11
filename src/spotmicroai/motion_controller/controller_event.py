from enum import Enum

class ControllerEvent(str, Enum):
    # --- Thumbsticks (analog) ---
    LEFT_STICK_X = "lx"              # Left thumbstick left/right
    LEFT_STICK_Y = "ly"              # Left thumbstick up/down
    RIGHT_STICK_Y = "lz"             # Right thumbstick up/down
    RIGHT_STICK_X = "rz"             # Right thumbstick left/right

    # --- Triggers (analog) ---
    RIGHT_TRIGGER = "gas"            # Right analog trigger
    LEFT_TRIGGER = "brake"           # Left analog trigger

    # --- D-Pad (HAT axes) ---
    DPAD_HORIZONTAL = "hat0x"        # -1 = left, +1 = right
    DPAD_VERTICAL = "hat0y"          # -1 = up, +1 = down

    # --- Face Buttons ---
    A = "a"
    B = "b"
    X = "x"
    Y = "y"

    # --- Bumpers & System Buttons ---
    LEFT_BUMPER = "tl"               # Left bumper button
    RIGHT_BUMPER = "tr"              # Right bumper button
    BACK = "select"                  # 'Select' on PS / 'Back' or 'View' on Xbox
    START = "start"                  # 'Start' / 'Menu' button
    LEFT_STICK_CLICK = "thumbl"      # Pressing left thumbstick (L3)
    RIGHT_STICK_CLICK = "thumbr"     # Pressing right thumbstick (R3)
