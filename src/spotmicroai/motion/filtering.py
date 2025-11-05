# rate_limited_first_order_filter.py


class RateLimitedFirstOrderFilter:
    """
    A first-order low-pass filter with an optional rate limiter.

    Used to smooth noisy or sudden input changes (like velocity or angle commands)
    so that outputs change gradually — avoiding jerky motion or actuator stress.

    Mathematical model:
        y[i] = (1 - α) * y[i-1] + α * u[i]
        α = dt / (τ + dt)

    - y[i]: current output (filtered signal)
    - y[i-1]: previous output
    - u[i]: current input (command)
    - τ (tau): time constant controlling responsiveness
    - dt: sample time (seconds)
    - α (alpha): blending factor computed from τ and dt

    A rate limit ensures |(y[i] - y[i-1]) / dt| ≤ rate_limit.
    """

    dt: float
    tau: float
    state: float
    command: float
    alpha: float
    rate_limit: float

    def __init__(self, dt: float = 0.001, tau: float = 1.0, x0: float = 0.0, rate_limit: float = float('inf')):
        """
        Initialize the filter with:
          dt         — sample time in seconds (e.g., 0.02 for 50 Hz update rate)
          tau (τ)    — time constant controlling how fast output follows input
          x0         — initial value of the signal at time 0 (startup value)
          rate_limit — maximum allowed rate of change (units per second)
                       use float('inf') for no rate limiting.
        """
        # Control loop period (seconds). At 50 Hz → dt = 0.02 s (20 ms)
        self.dt = dt

        # Time constant τ (seconds): controls smoothness vs. responsiveness.
        # Smaller τ → faster response. Larger τ → smoother, slower output.
        self.tau = tau

        # Internal filter output (y[i]): starts from x₀, the initial signal value.
        # Typically initialized to the system's current measurement at startup.
        self.state = x0

        # Command input (u[i]): the desired target the filter will approach.
        # Initialized to x₀ so the filter starts without any initial jump.
        self.command = x0

        # Blending factor α = dt / (τ + dt): fraction of new input mixed in each step.
        # Larger α → faster tracking; smaller α → smoother response.
        self.alpha = dt / (tau + dt)

        # Maximum allowed rate of change in output (units per second).
        # Prevents unrealistic jumps due to sudden command changes.
        self.rate_limit = rate_limit

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------

    def set_command(self, command: float):
        """Set a new desired (commanded) input value u[i]."""
        self.command = command

    def run_timestep(self):
        """
        Run one update step of the filter.

        1. Apply first-order low-pass filtering using α.
        2. Enforce the rate limit, ensuring output changes
           no faster than rate_limit * dt per step.
        """
        a = self.alpha
        y_prev = self.state
        u = self.command

        # --- Low-pass filtering ---
        # Smoothly blend previous output and current command.
        y = (1 - a) * y_prev + a * u

        # --- Rate limiting ---
        # Compute instantaneous rate of change.
        rate = (y - y_prev) / self.dt

        # Clamp the rate if it exceeds the maximum allowed speed.
        if abs(rate) > self.rate_limit:
            if rate > 0:
                y = y_prev + self.rate_limit * self.dt
            else:
                y = y_prev - self.rate_limit * self.dt

        # Update the internal state for the next iteration.
        self.state = y

    def run_timestep_and_get_output(self) -> float:
        """
        Run one timestep and return the new filtered output.

        Common pattern in control loops:
            output = filter.run_timestep_and_get_output()
        """
        self.run_timestep()
        return self.state

    def get_output(self) -> float:
        """Return the current filtered output value (y[i])."""
        return self.state

    def reset_state(self, x0: float):
        """
        Reset the internal state of the filter to a new initial value.
        Useful when restarting a control loop or reinitializing a robot.
        """
        self.state = x0


class XyzFilters:
    """Holds 3 filters for x, y, z axes.

    A simple container that groups three RateLimitedFirstOrderFilter instances,
    one for each spatial axis (x, y, z). Used to filter position or angle values
    along different axes independently.
    """

    x: RateLimitedFirstOrderFilter | None
    y: RateLimitedFirstOrderFilter | None
    z: RateLimitedFirstOrderFilter | None

    def __init__(
        self,
        x: RateLimitedFirstOrderFilter | None = None,
        y: RateLimitedFirstOrderFilter | None = None,
        z: RateLimitedFirstOrderFilter | None = None,
    ):
        """Initialize with three RateLimitedFirstOrderFilter instances.

        Args:
            x: RateLimitedFirstOrderFilter for x-axis filtering
            y: RateLimitedFirstOrderFilter for y-axis filtering
            z: RateLimitedFirstOrderFilter for z-axis filtering
        """
        self.x = x
        self.y = y
        self.z = z


class BodyStateFilters:
    """Container for all robot body filter groups.

    This is a simple container struct mirroring the C++ BodyStateFilters.
    Filters are initialized individually by the state machine, not through
    this constructor.
    """

    def __init__(self):
        """Initialize empty filter groups."""
        self.leg_right_back = XyzFilters()
        self.leg_right_front = XyzFilters()
        self.leg_left_front = XyzFilters()
        self.leg_left_back = XyzFilters()
        self.body_pos = XyzFilters()
        self.body_angs = XyzFilters()
