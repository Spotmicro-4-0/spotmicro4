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
