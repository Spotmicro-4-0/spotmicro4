from typing import Callable, Optional

from spotmicroai.runtime.motion_controller.debounced_button import DebouncedButton
from spotmicroai.runtime.motion_controller.models import ControllerEvent, ControllerEventKey
from spotmicroai.logger import Logger

log = Logger().setup_logger('ButtonManager')


class ButtonManager:
    """
    Manages multiple debounced buttons and provides edge detection for events.

    This class tracks button states across frames to detect button press events
    (transition from not pressed to pressed) and enforces debouncing per button.
    """

    # Mapping from ControllerEventKey enum to ControllerEvent attribute names
    _KEY_TO_ATTR = {
        ControllerEventKey.LEFT_STICK_X: "left_stick_x",
        ControllerEventKey.LEFT_STICK_Y: "left_stick_y",
        ControllerEventKey.RIGHT_STICK_X: "right_stick_x",
        ControllerEventKey.RIGHT_STICK_Y: "right_stick_y",
        ControllerEventKey.RIGHT_TRIGGER: "right_trigger",
        ControllerEventKey.LEFT_TRIGGER: "left_trigger",
        ControllerEventKey.DPAD_HORIZONTAL: "dpad_horizontal",
        ControllerEventKey.DPAD_VERTICAL: "dpad_vertical",
        ControllerEventKey.A: "a",
        ControllerEventKey.B: "b",
        ControllerEventKey.X: "x",
        ControllerEventKey.Y: "y",
        ControllerEventKey.LEFT_BUMPER: "left_bumper",
        ControllerEventKey.RIGHT_BUMPER: "right_bumper",
        ControllerEventKey.BACK: "back",
        ControllerEventKey.START: "start",
        ControllerEventKey.LEFT_STICK_CLICK: "left_stick_click",
        ControllerEventKey.RIGHT_STICK_CLICK: "right_stick_click",
    }

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

    def check_edge(self, key: ControllerEventKey, event: ControllerEvent) -> bool:
        """
        Check if a button/key transitioned from 0 to non-zero (edge detection).

        This is useful for buttons that don't need debouncing but need edge detection.

        Parameters
        ----------
        key : ControllerEventKey
            The event key to check
        event : ControllerEvent
            The current event object

        Returns
        -------
        bool
            True if the key transitioned from 0 to non-zero
        """
        # Get the attribute name from the key
        attr_name = self._KEY_TO_ATTR.get(key)
        if attr_name is None:
            log.debug(f"check_edge: Key {key} not found in mapping")
            return False

        # Get current and previous values
        current_value = getattr(event, attr_name, 0)
        previous_value = self._previous_event.get(key, 0)

        log.debug(f"check_edge: key={key}, attr={attr_name}, current={current_value}, prev={previous_value}")

        # Update previous event state
        self._previous_event[key] = current_value

        edge_detected = current_value != 0 and previous_value == 0
        if edge_detected:
            log.debug(f"check_edge: EDGE DETECTED for {key}")

        return edge_detected

    def reset(self):
        """Reset all button states and previous event tracking."""
        for button in self._buttons.values():
            button.reset()
        self._previous_event.clear()
