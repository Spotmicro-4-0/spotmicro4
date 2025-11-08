from typing import Callable, Optional

from spotmicroai.runtime.motion_controller.debounced_button import DebouncedButton
from spotmicroai.runtime.motion_controller.models import ControllerEvent


class ButtonManager:
    """
    Manages multiple debounced buttons and provides edge detection for events.

    This class tracks button states across frames to detect button press events
    (transition from not pressed to pressed) and enforces debouncing per button.
    """

    def __init__(self):
        """Initialize the button manager."""
        self._buttons = {}
        self._previous_event = {}

    def register_button(
        self, key: str, debounce_time: float = 1.0, on_press: Optional[Callable] = None
    ) -> DebouncedButton:
        """
        Register a new debounced button.

        Parameters
        ----------
        key : str
            The event key this button listens for
        debounce_time : float
            Minimum time in seconds between triggers
        on_press : Optional[Callable]
            Callback function to execute when button is pressed

        Returns
        -------
        DebouncedButton
            The registered button instance
        """
        button = DebouncedButton(key, debounce_time, on_press)
        self._buttons[key] = button
        return button

    def update(self, event: dict) -> bool:
        """
        Update all registered buttons with the current event.

        Parameters
        ----------
        event : dict
            The current event dictionary

        Returns
        -------
        bool
            True if any registered button was pressed
        """
        any_pressed = False
        for button in self._buttons.values():
            if button.update(event):
                any_pressed = True
        return any_pressed

    def is_pressed(self, key: str, event: dict) -> bool:
        """
        Check if a registered button was pressed (with debouncing).

        Parameters
        ----------
        key : str
            The event key to check
        event : dict
            The current event dictionary

        Returns
        -------
        bool
            True if button was pressed and debounce time has passed
        """
        if key in self._buttons:
            return self._buttons[key].update(event)
        return False

    def check_edge(self, key: str, event: ControllerEvent) -> bool:
        """
        Check if a button/key transitioned from 0 to non-zero (edge detection).

        This is useful for buttons that don't need debouncing but need edge detection.

        Parameters
        ----------
        key : str
            The event key to check
        event : dict
            The current event dictionary

        Returns
        -------
        bool
            True if the key transitioned from 0 to non-zero
        """
        current_value = event.get(key, 0)
        previous_value = self._previous_event.get(key, 0)

        # Update previous event state
        self._previous_event[key] = current_value

        return current_value != 0 and previous_value == 0

    def reset(self):
        """Reset all button states and previous event tracking."""
        for button in self._buttons.values():
            button.reset()
        self._previous_event.clear()
