from spotmicroai.runtime.controller_event import ControllerEvent

from .filtered_analog_axis import FilteredAnalogAxis
from .debounced_button import DebouncedButton


class FilteredControllerEvent:
    """
    Systematically applies filtering (for analog) and debouncing (for digital)
    to a ControllerEvent object.
    """
    def __init__(self):
        self._left_stick_x = FilteredAnalogAxis()
        self._left_stick_y = FilteredAnalogAxis()
        self._right_stick_x = FilteredAnalogAxis()
        self._right_stick_y = FilteredAnalogAxis()

        # Triggers (analog)
        self._right_trigger = FilteredAnalogAxis()
        self._left_trigger = FilteredAnalogAxis()

        # D-Pad (digital)
        self._dpad_horizontal = FilteredAnalogAxis()
        self._dpad_vertical = FilteredAnalogAxis()

        # Face buttons (digital)
        self._a = DebouncedButton()
        self._b = DebouncedButton()
        self._x = DebouncedButton()
        self._y = DebouncedButton()

        # Bumpers & system buttons (digital)
        self._left_bumper = DebouncedButton()
        self._right_bumper = DebouncedButton()
        self._back = DebouncedButton()
        self._start = DebouncedButton()
        self._left_stick_click = DebouncedButton()
        self._right_stick_click = DebouncedButton()

    # ----------------------------------------------------------------------
    def update(self, event: ControllerEvent) -> None:
        """
        Process a new raw ControllerEvent (e.g., from a joystick)
        and update all filters and debouncers in place.
        """

        # Thumbsticks (analog)
        self._left_stick_x.update(event.left_stick_x)
        self._left_stick_y.update(event.left_stick_y)
        self._right_stick_x.update(event.right_stick_x)
        self._right_stick_y.update(event.right_stick_y)

        # Triggers (analog)
        self._right_trigger.update(event.right_trigger)
        self._left_trigger.update(event.left_trigger)

        # D-Pad (digital/analog)
        self._dpad_horizontal.update(event.dpad_horizontal)
        self._dpad_vertical.update(event.dpad_vertical)

        # Face buttons (digital)
        self._a.update(event.a)
        self._b.update(event.b)
        self._x.update(event.x)
        self._y.update(event.y)

        # Bumpers & system buttons (digital)
        self._left_bumper.update(event.left_bumper)
        self._right_bumper.update(event.right_bumper)
        self._back.update(event.back)
        self._start.update(event.start)
        self._left_stick_click.update(event.left_stick_click)
        self._right_stick_click.update(event.right_stick_click)

    # ----------------------------------------------------------------------

    def reset(self):
        """Reset all underlying filter/debounce states."""

        # Thumbsticks (analog)
        self._left_stick_x.reset()
        self._left_stick_y.reset()
        self._right_stick_x.reset()
        self._right_stick_y.reset()

        # Triggers (analog)
        self._right_trigger.reset()
        self._left_trigger.reset()

        # D-Pad (digital)
        self._dpad_horizontal.reset()
        self._dpad_vertical.reset()

        # Face buttons (digital)
        self._a.reset()
        self._b.reset()
        self._x.reset()
        self._y.reset()

        # Bumpers & system buttons (digital)
        self._left_bumper.reset()
        self._right_bumper.reset()
        self._back.reset()
        self._start.reset()
        self._left_stick_click.reset()
        self._right_stick_click.reset()

    @property
    def left_stick_x(self):
        return self._left_stick_x.value

    @property
    def left_stick_y(self):
        return self._left_stick_y.value

    @property
    def right_stick_x(self):
        return self._right_stick_x.value

    @property
    def right_stick_y(self):
        return self._right_stick_y.value

    @property
    def right_trigger(self):
        return self._right_trigger.value

    @property
    def left_trigger(self):
        return self._left_trigger.value

    @property
    def dpad_horizontal(self):
        return self._dpad_horizontal.value

    @property
    def dpad_vertical(self):
        return self._dpad_vertical.value

    @property
    def a(self):
        return self._a.value

    @property
    def b(self):
        return self._b.value

    @property
    def x(self):
        return self._x.value

    @property
    def y(self):
        return self._y.value

    @property
    def left_bumper(self):
        return self._left_bumper.value

    @property
    def right_bumper(self):
        return self._right_bumper.value

    @property
    def back(self):
        return self._back.value

    @property
    def start(self):
        return self._start.value

    @property
    def left_stick_click(self):
        return self._left_stick_click.value

    @property
    def right_stick_click(self):
        return self._right_stick_click.value

    def has_activity(self, threshold: float = 0.01) -> bool:
        """
        Check if there's any active user input (analog or digital).

        Args:
            threshold: Minimum absolute value for analog inputs to be considered active

        Returns:
            True if any input is active, False otherwise
        """
        return (
            abs(self.left_stick_x) > threshold
            or abs(self.left_stick_y) > threshold
            or abs(self.right_stick_x) > threshold
            or abs(self.right_stick_y) > threshold
            or abs(self.right_trigger) > threshold
            or abs(self.left_trigger) > threshold
            or self.dpad_horizontal != 0
            or self.dpad_vertical != 0
            or self.a
            or self.b
            or self.x
            or self.y
            or self.left_bumper
            or self.right_bumper
            or self.back
            or self.left_stick_click
            or self.right_stick_click
        )

    @property
    def value(self):
        return ControllerEvent(
            left_stick_x=self.left_stick_x,
            left_stick_y=self.left_stick_y,
            right_stick_x=self.right_stick_x,
            right_stick_y=self.right_stick_y,
            right_trigger=self.right_trigger,
            left_trigger=self.left_trigger,
            dpad_horizontal=int(self.dpad_horizontal),
            dpad_vertical=int(self.dpad_vertical),
            a=self.a,
            b=self.b,
            x=self.x,
            y=self.y,
            left_bumper=self.left_bumper,
            right_bumper=self.right_bumper,
            back=self.back,
            start=self.start,
            left_stick_click=self.left_stick_click,
            right_stick_click=self.right_stick_click,
        )
