# command.py


class Command:
    """
    Encapsulates motion and state commands for the robot.

    Contains both continuous control targets (velocities, orientation angles)
    and discrete mode/event flags (idle, walk, stand). This object is typically
    passed into the motion controller or finite state machine each control tick.
    """

    def __init__(
        self,
        x_velocity: float = 0.0,  # m/s
        y_velocity: float = 0.0,  # m/s
        yaw_rate: float = 0.0,  # rps
        phi: float = 0.0,
        theta: float = 0.0,
        psi: float = 0.0,
        idle: bool = False,
        walk: bool = False,
        stand: bool = False,
    ):
        # --- Linear velocity commands ---

        # Desired velocity along the robot's X-axis (forward/backward motion).
        # Unit: meters per second (m/s).
        # Positive values move the robot forward; negative values move it backward.
        self._x_velocity = x_velocity

        # Desired velocity along the robot's Y-axis (lateral motion).
        # Unit: meters per second (m/s).
        # Positive values strafe to the robot's right; negative values strafe left.
        self._y_velocity = y_velocity

        # Desired rotational velocity about the robot's Z-axis (turning rate).
        # Unit: radians per second (rad/s).
        # Positive values rotate the robot counterclockwise (turn left).
        self._yaw_rate = yaw_rate

        # --- Body orientation commands (Euler angles) ---

        # φ (phi): Roll angle — rotation around the X-axis.
        # Tilts the robot side-to-side. Unit: radians.
        self._phi = phi

        # θ (theta): Pitch angle — rotation around the Y-axis.
        # Tilts the robot forward/backward. Unit: radians.
        self._theta = theta

        # ψ (psi): Yaw angle — rotation around the Z-axis.
        # Rotates the robot’s body orientation (heading). Unit: radians.
        self._psi = psi

        # --- Discrete event/mode commands ---

        # True when the controller requests the robot to enter idle mode (rest posture).
        self._idle = idle

        # True when the controller requests the robot to begin or continue walking.
        self._walk = walk

        # True when the controller requests the robot to stand upright and stabilize.
        self._stand = stand

    # --- Properties (read-only accessors) ---

    @property
    def stand(self) -> bool:
        """Return True if the stand command is active."""
        return self._stand

    @property
    def idle(self) -> bool:
        """Return True if the idle command is active."""
        return self._idle

    @property
    def walk(self) -> bool:
        """Return True if the walk command is active."""
        return self._walk

    @property
    def x_velocity(self) -> float:
        """Forward/backward velocity command along X-axis (m/s)."""
        return self._x_velocity

    @property
    def y_velocity(self) -> float:
        """Lateral (sideways) velocity command along Y-axis (m/s)."""
        return self._y_velocity

    @property
    def yaw_rate(self) -> float:
        """Rotational velocity command around Z-axis (rad/s)."""
        return self._yaw_rate

    @property
    def phi(self) -> float:
        """Roll angle command (rotation around X-axis, radians)."""
        return self._phi

    @property
    def theta(self) -> float:
        """Pitch angle command (rotation around Y-axis, radians)."""
        return self._theta

    @property
    def psi(self) -> float:
        """Yaw angle command (rotation around Z-axis, radians)."""
        return self._psi

    # --- Mutating methods ---

    def reset_all_commands(self):
        """Reset all continuous (numeric) commands to zero."""
        self._x_velocity = 0.0
        self._y_velocity = 0.0
        self._yaw_rate = 0.0
        self._phi = 0.0
        self._theta = 0.0
        self._psi = 0.0

    def reset_event_commands(self):
        """Reset all discrete (boolean) commands to False."""
        self._idle = False
        self._walk = False
        self._stand = False

    # --- Utility ---

    def __repr__(self):
        return (
            f"x={self._x_velocity:.2f} m/s, "
            f"y={self._y_velocity:.2f} m/s, yaw_rate={self._yaw_rate:.2f} rad/s, "
            f"stand={self._stand}, walk={self._walk}, idle={self._idle}>"
        )
