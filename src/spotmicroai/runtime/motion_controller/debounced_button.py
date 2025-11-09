"""
Debounced button handler for managing button state and preventing rapid re-triggers.
"""

import time
from typing import Callable, Optional

import spotmicroai.constants as constants


class DebouncedButton:
    """
    A button handler that tracks state and enforces debouncing.

    Attributes
    ----------
    key : str
        The event key this button listens for
    debounce_time : float
        Minimum time in seconds between triggers (default: 1.0)
    on_press : Optional[Callable]
        Callback function to execute when button is pressed
    """

    def __init__(self, debounce_time: float = constants.DEFAULT_DEBOUNCE_TIME, on_press: Optional[Callable] = None):
        """
        Initialize a debounced button.

        Parameters
        ----------
        key : str
            The event key this button listens for
        debounce_time : float
            Minimum time in seconds between triggers
        on_press : Optional[Callable]
            Callback function to execute when button is pressed
        """
        self.debounce_time = debounce_time
        self.on_press = on_press
        self._last_trigger_time = 0.0
        self._previous_value = 0.0
        self._is_pressed = False

    def update(self, current_value: bool) -> None:
        """
        Update button state and check if it was pressed.

        Parameters
        ----------
        event : dict
            The current event dictionary

        Returns
        -------
        bool
            True if button was pressed and debounce time has passed, False otherwise
        """
        # Check if button was just pressed (transition from 0 to non-zero)
        self._is_pressed = current_value != 0 and self._previous_value == 0

        # Update previous value for next check
        self._previous_value = current_value

        if self._is_pressed:
            # Check debounce timing
            current_time = time.time()
            if current_time - self._last_trigger_time >= self.debounce_time:
                self._last_trigger_time = current_time

                # Execute callback if provided
                if self.on_press:
                    self.on_press()

    def reset(self):
        """Reset the button state and debounce timer."""
        self._last_trigger_time = 0
        self._previous_value = 0

    @property
    def value(self):
        return self._is_pressed
