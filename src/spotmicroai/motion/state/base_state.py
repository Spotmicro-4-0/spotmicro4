from abc import ABC, abstractmethod

from spotmicroai.motion.command import Command
from spotmicroai.motion.filtering import BodyStateFilters, RateLimitedFirstOrderFilter, XyzFilters
from spotmicroai.motion.models import BodyState
from spotmicroai.runtime.motion_controller.motion_controller import MotionController


class BaseState(ABC):

    # -----------------------------------------------------------------
    # Abstract methods to be implemented by derived classes
    # -----------------------------------------------------------------

    @abstractmethod
    def handle_input_commands(
        self,
        body_state: BodyState,
        command: Command,
        motion_controller: "MotionController",
        body_state_cmd: BodyState,
    ) -> None:
        """Handle input commands."""

    @abstractmethod
    def init(self, body_state: BodyState, command: "Command", motion_controller: "MotionController") -> None:
        """Initialize state."""

    @abstractmethod
    def get_current_state_name(self) -> str:
        """Return current state name."""

    # -----------------------------------------------------------------
    # Protected methods (used by derived classes)
    # -----------------------------------------------------------------

    def change_state(self, motion_controller: "MotionController", new_state: "BaseState") -> None:
        """Change the MotionController's internal state."""
        motion_controller.change_state(new_state)

    # -----------------------------------------------------------------
    def init_body_state_filters(self, dt, tau, rl, rl_ang, body_state: BodyState, body_state_filters: BodyStateFilters):
        """Initialize a set of filters controlling body state values."""
        legs = body_state.legs_foot_positions

        body_state_filters.leg_right_front = XyzFilters(
            x=RateLimitedFirstOrderFilter(dt, tau, legs.right_front.x, rl),
            y=RateLimitedFirstOrderFilter(dt, tau, legs.right_front.y, rl),
            z=RateLimitedFirstOrderFilter(dt, tau, legs.right_front.z, rl),
        )
        body_state_filters.leg_right_back = XyzFilters(
            x=RateLimitedFirstOrderFilter(dt, tau, legs.right_back.x, rl),
            y=RateLimitedFirstOrderFilter(dt, tau, legs.right_back.y, rl),
            z=RateLimitedFirstOrderFilter(dt, tau, legs.right_back.z, rl),
        )
        body_state_filters.leg_left_back = XyzFilters(
            x=RateLimitedFirstOrderFilter(dt, tau, legs.left_back.x, rl),
            y=RateLimitedFirstOrderFilter(dt, tau, legs.left_back.y, rl),
            z=RateLimitedFirstOrderFilter(dt, tau, legs.left_back.z, rl),
        )
        body_state_filters.leg_left_front = XyzFilters(
            x=RateLimitedFirstOrderFilter(dt, tau, legs.left_front.x, rl),
            y=RateLimitedFirstOrderFilter(dt, tau, legs.left_front.y, rl),
            z=RateLimitedFirstOrderFilter(dt, tau, legs.left_front.z, rl),
        )

        pos = body_state.xyz_positions
        body_state_filters.body_pos = XyzFilters(
            x=RateLimitedFirstOrderFilter(dt, tau, pos.x, rl),
            y=RateLimitedFirstOrderFilter(dt, tau, pos.y, rl),
            z=RateLimitedFirstOrderFilter(dt, tau, pos.z, rl),
        )

        angs = body_state.euler_angles
        body_state_filters.body_angs = XyzFilters(
            x=RateLimitedFirstOrderFilter(dt, tau, angs.phi, rl_ang),
            y=RateLimitedFirstOrderFilter(dt, tau, angs.theta, rl_ang),
            z=RateLimitedFirstOrderFilter(dt, tau, angs.psi, rl_ang),
        )

    # -----------------------------------------------------------------
    def set_body_state_filter_commands(self, body_state: BodyState, body_state_filters: BodyStateFilters):
        """Set commands for all filters."""
        legs = body_state.legs_foot_positions

        # Right Front leg
        if body_state_filters.leg_right_front.x:
            body_state_filters.leg_right_front.x.set_command(legs.right_front.x)
        if body_state_filters.leg_right_front.y:
            body_state_filters.leg_right_front.y.set_command(legs.right_front.y)
        if body_state_filters.leg_right_front.z:
            body_state_filters.leg_right_front.z.set_command(legs.right_front.z)

        # Right Back leg
        if body_state_filters.leg_right_back.x:
            body_state_filters.leg_right_back.x.set_command(legs.right_back.x)
        if body_state_filters.leg_right_back.y:
            body_state_filters.leg_right_back.y.set_command(legs.right_back.y)
        if body_state_filters.leg_right_back.z:
            body_state_filters.leg_right_back.z.set_command(legs.right_back.z)

        # Left Back leg
        if body_state_filters.leg_left_back.x:
            body_state_filters.leg_left_back.x.set_command(legs.left_back.x)
        if body_state_filters.leg_left_back.y:
            body_state_filters.leg_left_back.y.set_command(legs.left_back.y)
        if body_state_filters.leg_left_back.z:
            body_state_filters.leg_left_back.z.set_command(legs.left_back.z)

        # Left Front leg
        if body_state_filters.leg_left_front.x:
            body_state_filters.leg_left_front.x.set_command(legs.left_front.x)
        if body_state_filters.leg_left_front.y:
            body_state_filters.leg_left_front.y.set_command(legs.left_front.y)
        if body_state_filters.leg_left_front.z:
            body_state_filters.leg_left_front.z.set_command(legs.left_front.z)

        # Body position
        pos = body_state.xyz_positions
        if body_state_filters.body_pos.x:
            body_state_filters.body_pos.x.set_command(pos.x)
        if body_state_filters.body_pos.y:
            body_state_filters.body_pos.y.set_command(pos.y)
        if body_state_filters.body_pos.z:
            body_state_filters.body_pos.z.set_command(pos.z)

        # Body angles
        angs = body_state.euler_angles
        if body_state_filters.body_angs.x:
            body_state_filters.body_angs.x.set_command(angs.phi)
        if body_state_filters.body_angs.y:
            body_state_filters.body_angs.y.set_command(angs.theta)
        if body_state_filters.body_angs.z:
            body_state_filters.body_angs.z.set_command(angs.psi)

    # -----------------------------------------------------------------
    def run_filters(self, body_state_filters: BodyStateFilters):
        """Run a timestep for all filters."""
        for group in [
            body_state_filters.body_pos,
            body_state_filters.body_angs,
            body_state_filters.leg_right_back,
            body_state_filters.leg_right_front,
            body_state_filters.leg_left_front,
            body_state_filters.leg_left_back,
        ]:
            if group.x:
                group.x.run_timestep()
            if group.y:
                group.y.run_timestep()
            if group.z:
                group.z.run_timestep()

    # -----------------------------------------------------------------
    def assign_filter_values_to_body_state(self, body_state_filters: BodyStateFilters, body_state: BodyState):
        """Assign current filter outputs back into the body state."""
        pos = body_state.xyz_positions
        if body_state_filters.body_pos.x:
            pos.x = body_state_filters.body_pos.x.get_output()
        if body_state_filters.body_pos.y:
            pos.y = body_state_filters.body_pos.y.get_output()
        if body_state_filters.body_pos.z:
            pos.z = body_state_filters.body_pos.z.get_output()

        angs = body_state.euler_angles
        if body_state_filters.body_angs.x:
            angs.phi = body_state_filters.body_angs.x.get_output()
        if body_state_filters.body_angs.y:
            angs.theta = body_state_filters.body_angs.y.get_output()
        if body_state_filters.body_angs.z:
            angs.psi = body_state_filters.body_angs.z.get_output()

        # Legs
        legs = body_state.legs_foot_positions
        for leg_name in ["right_back", "right_front", "left_front", "left_back"]:
            leg = getattr(legs, leg_name)
            f = getattr(body_state_filters, f"leg_{leg_name}")
            if f.x:
                leg.x = f.x.get_output()
            if f.y:
                leg.y = f.y.get_output()
            if f.z:
                leg.z = f.z.get_output()

    # -----------------------------------------------------------------
    def check_body_state_equality(self, body_state1: BodyState, body_state2: BodyState, tol: float) -> bool:
        """Check equality of two BodyState instances within tolerance."""

        def close(a, b):
            return abs(a - b) <= tol

        bs1, bs2 = body_state1, body_state2

        # Check all leg positions
        for leg_name in ["right_back", "right_front", "left_front", "left_back"]:
            leg1 = getattr(bs1.legs_foot_positions, leg_name)
            leg2 = getattr(bs2.legs_foot_positions, leg_name)
            if not (close(leg1.x, leg2.x) and close(leg1.y, leg2.y) and close(leg1.z, leg2.z)):
                return False

        # Check body position
        pos1, pos2 = bs1.xyz_positions, bs2.xyz_positions
        if not (close(pos1.x, pos2.x) and close(pos1.y, pos2.y) and close(pos1.z, pos2.z)):
            return False

        # Check body angles
        ang1, ang2 = bs1.euler_angles, bs2.euler_angles
        if not (close(ang1.phi, ang2.phi) and close(ang1.theta, ang2.theta) and close(ang1.psi, ang2.psi)):
            return False

        return True
