from spotmicroai.configuration._parameters_provider import ParametersProvider
from spotmicroai.runtime.motion_controller.inverse_kinematics import BodyState, FeetPositions, Position

class FilteredValue:
    """A value that automatically applies filtering on step.

    Usage:
        fv = FilteredValue(dt=0.01, tau=0.5, rate_limit=0.1)
        fv.value = 0.5          # Stage the new value
        fv.value = 0.7          # Stage another value
        fv.step()               # Apply filter timestep
        print(fv.get())         # Get filtered output
    """

    _delta_time: float
    _smoothing_factor: float
    _value: float
    _target_value: float | None
    _blending_factor: float
    _rate_limit: float
    _convergence_epsilon: float

    def __init__(
        self,
        delta_time: float = 0.001,
        smoothing_factor: float = 1.0,
        initial_value: float = 0.0,
        rate_limit: float = float('inf'),
        convergence_epsilon: float = 0.01,
    ):
        """Initialize filter.

        Args:
            delta_time: Sample period in seconds
            smoothing_factor: Time constant τ controlling responsiveness
            initial_value: Starting output value
            rate_limit: Maximum rate of change per second
            convergence_epsilon: Threshold for detecting convergence
        """
        # Control loop period (seconds). At 50 Hz → dt = 0.02 s (20 ms)
        self._delta_time = delta_time

        # Time constant τ (seconds): controls smoothness vs. responsiveness.
        # Smaller τ → faster response. Larger τ → smoother, slower output.
        self._smoothing_factor = smoothing_factor

        # Internal filter output (y[i]): starts from x₀, the initial signal value.
        # Typically initialized to the system's current measurement at startup.
        self._value = initial_value

        # Command input (u[i]): the desired target the filter will approach.
        # None when idle, set to target value when active filtering is needed.
        self._target_value = None

        # Blending factor α = dt / (τ + dt): fraction of new input mixed in each step.
        # Larger α → faster tracking; smaller α → smoother response.
        self._blending_factor = delta_time / (smoothing_factor + delta_time)

        # Maximum allowed rate of change in output (units per second).
        # Prevents unrealistic jumps due to sudden command changes.
        self._rate_limit = rate_limit

        # Convergence threshold: when abs(value - target) < epsilon, filtering stops.
        self._convergence_epsilon = convergence_epsilon

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------
    @property
    def value(self) -> float:
        """Return current filtered output value."""
        return self._value

    @value.setter
    def value(self, new_value: float) -> None:
        """Stage new target value for next filter step."""
        self._target_value = new_value

    def step(self) -> float:
        """Execute one filter update step with low-pass filtering and rate limiting."""
        # No active target: return current value without computation.
        if self._target_value is None:
            return self._value

        a = self._blending_factor
        y_prev = self._value
        u = self._target_value
        assert u is not None

        # --- Low-pass filtering ---
        # Smoothly blend previous output and current command.
        y = (1 - a) * y_prev + a * u

        # --- Rate limiting ---
        # Compute instantaneous rate of change.
        rate = (y - y_prev) / self._delta_time

        # Clamp the rate if it exceeds the maximum allowed speed.
        if abs(rate) > self._rate_limit:
            if rate > 0:
                y = y_prev + self._rate_limit * self._delta_time
            else:
                y = y_prev - self._rate_limit * self._delta_time

        # Update the internal state for the next iteration.
        self._value = y

        # Check convergence: if close enough to target, stop filtering.
        if abs(self._value - u) < self._convergence_epsilon:
            self._target_value = None

        return self._value

    def reset(self, initial_value: float):
        """Reset filter state to new initial value."""
        self._value = initial_value
        self._target_value = initial_value


class FilteredPosition:
    """Three-axis filter container for x, y, z coordinates.

    Groups three independent filters for filtering position or angle values.
    """

    _x: FilteredValue
    _y: FilteredValue
    _z: FilteredValue

    def __init__(
        self,
        delta_time: float,
        smoothing_factor: float,
        rate_limit: float,
        initial_value: Position | None = None,
    ):
        if initial_value is None:
            initial_value = Position()

        self._x = FilteredValue(
            delta_time=delta_time,
            smoothing_factor=smoothing_factor,
            rate_limit=rate_limit,
            initial_value=initial_value.x,
        )
        self._y = FilteredValue(
            delta_time=delta_time,
            smoothing_factor=smoothing_factor,
            rate_limit=rate_limit,
            initial_value=initial_value.y,
        )
        self._z = FilteredValue(
            delta_time=delta_time,
            smoothing_factor=smoothing_factor,
            rate_limit=rate_limit,
            initial_value=initial_value.z,
        )

    @property
    def value(self) -> Position:
        """Return current filtered position value."""
        return Position(self._x.value, self._y.value, self._z.value)

    @value.setter
    def value(self, position: Position):
        """Request a new position value"""
        self._x.value = position.x
        self._y.value = position.y
        self._z.value = position.z

    def step(self):
        """Execute one filter update step for all axes."""
        self._x.step()
        self._y.step()
        self._z.step()

    def reset(self, position: Position):
        """Reset all axes to given position."""
        self._x.reset(position.x)
        self._y.reset(position.y)
        self._z.reset(position.z)


class FilteredFeetPositions:
    """Filter container for all four feet positions.

    Groups four independent FilteredPosition instances for each leg.
    """

    _front_left: FilteredPosition
    _front_right: FilteredPosition
    _rear_left: FilteredPosition
    _rear_right: FilteredPosition

    def __init__(
        self,
        delta_time: float,
        smoothing_factor: float,
        rate_limit: float,
        initial_value: FeetPositions | None = None,
    ):
        if initial_value is None:
            initial_value = FeetPositions()

        self._front_left = FilteredPosition(delta_time, smoothing_factor, rate_limit, initial_value.front_left)
        self._front_right = FilteredPosition(delta_time, smoothing_factor, rate_limit, initial_value.front_right)
        self._rear_left = FilteredPosition(delta_time, smoothing_factor, rate_limit, initial_value.rear_left)
        self._rear_right = FilteredPosition(delta_time, smoothing_factor, rate_limit, initial_value.rear_right)

    @property
    def value(self) -> FeetPositions:
        """Return current filtered feet positions."""
        return FeetPositions(
            front_left=self._front_left.value,
            front_right=self._front_right.value,
            rear_left=self._rear_left.value,
            rear_right=self._rear_right.value,
        )

    @value.setter
    def value(self, feet_positions: FeetPositions):
        """Request new feet positions."""
        self._front_left.value = feet_positions.front_left
        self._front_right.value = feet_positions.front_right
        self._rear_left.value = feet_positions.rear_left
        self._rear_right.value = feet_positions.rear_right

    def step(self):
        """Execute one filter update step for all feet."""
        self._front_left.step()
        self._front_right.step()
        self._rear_left.step()
        self._rear_right.step()

    def reset(self, feet_positions: FeetPositions):
        """Reset all feet filters to given positions."""
        self._front_left.reset(feet_positions.front_left)
        self._front_right.reset(feet_positions.front_right)
        self._rear_left.reset(feet_positions.rear_left)
        self._rear_right.reset(feet_positions.rear_right)


class FilteredBodyState:
    """Filter groups for all robot body state components.

    Contains FilteredPosition instances for each leg and body pose.
    """

    def __init__(self, initial_value: BodyState | None = None):
        parameters_provider = ParametersProvider()
        delta_time = parameters_provider.dt
        smoothing_factor = parameters_provider.transit_tau
        rate_limit = parameters_provider.transit_rl
        angle_rate_limit = parameters_provider.transit_angle_rl

        if initial_value is None:
            initial_value = BodyState()

        self._omega = FilteredValue(delta_time, smoothing_factor, angle_rate_limit, initial_value.omega)
        self._phi = FilteredValue(delta_time, smoothing_factor, angle_rate_limit, initial_value.phi)
        self._psi = FilteredValue(delta_time, smoothing_factor, angle_rate_limit, initial_value.psi)
        self._body_position = FilteredPosition(delta_time, smoothing_factor, rate_limit, initial_value.body_position)
        self._feet_positions = FilteredFeetPositions(
            delta_time, smoothing_factor, rate_limit, initial_value.feet_positions
        )

    @property
    def value(self) -> BodyState:
        """Get all current filtered values."""
        return BodyState(
            omega=self._omega.value,
            phi=self._phi.value,
            psi=self._psi.value,
            body_position=self._body_position.value,
            feet_positions=self._feet_positions.value,
        )

    @value.setter
    def value(self, value: BodyState) -> None:
        """Stage next target values for all body state components."""
        self._omega.value = value.omega
        self._phi.value = value.phi
        self._psi.value = value.psi
        self._body_position.value = value.body_position
        self._feet_positions.value = value.feet_positions

    def step(self):
        """Step all filters by one iteration."""
        self._omega.step()
        self._phi.step()
        self._psi.step()
        self._body_position.step()
        self._feet_positions.step()

    def reset(self, initial_state: BodyState):
        """Reset all filters to given initial values."""
        self._omega.reset(initial_state.omega)
        self._phi.reset(initial_state.phi)
        self._psi.reset(initial_state.psi)
        self._body_position.reset(initial_state.body_position)
        self._feet_positions.reset(initial_state.feet_positions)
