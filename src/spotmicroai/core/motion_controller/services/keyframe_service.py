import math
import time
from typing import List, Tuple

from spotmicroai.core.motion_controller.constants import (
    HEIGHT_MULTIPLIER,
    LEAN_MULTIPLIER,
    MAX_WALKING_SPEED,
    ROTATION_INCREMENT,
    ROTATION_OFFSET,
)
from spotmicroai.core.motion_controller.models.coordinate import Coordinate
from spotmicroai.core.motion_controller.models.keyframe import Keyframe
from spotmicroai.core.utilities.config import Config
from spotmicroai.core.utilities.singleton import Singleton


class KeyframeService(metaclass=Singleton):
    """A class representing a transition from a previous keyframe to a next keyframe.

    Attributes:
        _next: The next keyframe (Keyframe).
        _previous: The previous keyframe (Keyframe).
    """

    _walking_cycle: List[Coordinate] = []
    __next_keyframe: Keyframe
    __previous_keyframe: Keyframe

    def __init__(self):
        self.__next_keyframe = Keyframe()
        self.__previous_keyframe = Keyframe()

        self._forward_factor = 0.0
        self._max_forward_factor = 0.5
        self._rotation_factor = 0.0
        self._lean_factor = 0.0
        self._height_factor = 1.0
        self._walking_speed = 10.0

        # Walking state tracking
        self._elapsed = 0.0
        self._start = 0.0
        self.prev_index = 0

        if not self._walking_cycle:
            config = Config()
            walking_cycle_data = config.motion_controller.walking_cycle
            self.__class__._walking_cycle = [Coordinate(*pos) for pos in walking_cycle_data]

    @property
    def forward_factor(self) -> float:
        return self._forward_factor

    @forward_factor.setter
    def forward_factor(self, value: float):
        self._forward_factor = value

    @property
    def max_forward_factor(self) -> float:
        return self._max_forward_factor

    @max_forward_factor.setter
    def max_forward_factor(self, value: float):
        self._max_forward_factor = value

    @property
    def rotation_factor(self) -> float:
        return self._rotation_factor

    @rotation_factor.setter
    def rotation_factor(self, value: float):
        self._rotation_factor = value

    @property
    def lean_factor(self) -> float:
        return self._lean_factor

    @lean_factor.setter
    def lean_factor(self, value: float):
        self._lean_factor = value

    @property
    def height_factor(self) -> float:
        return self._height_factor

    @height_factor.setter
    def height_factor(self, value: float):
        self._height_factor = value

    @property
    def walking_speed(self) -> float:
        return self._walking_speed

    @walking_speed.setter
    def walking_speed(self, value: float):
        self._walking_speed = value

    @property
    def elapsed(self) -> float:
        return self._elapsed

    def _compute_rotation_offsets(self, x: float) -> Tuple[float, float]:
        """Calculate the rotational movement for a given x value

        Parameters
        ----------
        x : float
            The x value for the next keyframe

        Returns
        -------
        Tuple[float, float]
            A tuple of (x_rot, z_rot) representing the rotational offsets.
        """
        # This angle calculation is only used when rotating the bot clockwise or counter clockwise
        angle = 45.0 / 180.0 * math.pi
        x_rot = math.sin(angle) * self._rotation_factor * ROTATION_OFFSET
        z_rot = math.cos(angle) * self._rotation_factor * ROTATION_OFFSET

        angle = (45 + x) / 180.0 * math.pi
        x_rot = x_rot - math.sin(angle) * self._rotation_factor * ROTATION_OFFSET
        z_rot = z_rot - math.cos(angle) * self._rotation_factor * ROTATION_OFFSET

        return x_rot, z_rot

    def _advance_to_next_keyframe(self, next_index: int):
        current_coordinate = self._walking_cycle[next_index]

        # Calculate rotational movement for current index
        x_rot, z_rot = self._compute_rotation_offsets(current_coordinate.x)

        # Handle Front-Right and Back-Left legs first
        front_right = Coordinate(
            current_coordinate.x * -self._forward_factor + x_rot,
            current_coordinate.y,
            current_coordinate.z + z_rot,
        )

        rear_left = Coordinate(
            current_coordinate.x * -self._forward_factor - x_rot,
            current_coordinate.y,
            current_coordinate.z + z_rot,
        )

        # Handle the other two legs (Front-Left and Back-Right) with phase offset
        adjusted_index = (next_index + 3) % len(self._walking_cycle)
        current_coordinate = self._walking_cycle[adjusted_index]

        x_rot, z_rot = self._compute_rotation_offsets(current_coordinate.x)

        front_left = Coordinate(
            current_coordinate.x * -self._forward_factor - x_rot,
            current_coordinate.y,
            current_coordinate.z - z_rot,
        )

        rear_right = Coordinate(
            current_coordinate.x * -self._forward_factor + x_rot,
            current_coordinate.y,
            current_coordinate.z - z_rot,
        )

        # Shift keyframes: current becomes previous, prepare new current
        self.__previous_keyframe = self.__next_keyframe
        self.__next_keyframe = Keyframe(
            front_left=front_left, front_right=front_right, rear_left=rear_left, rear_right=rear_right
        )

        self.prev_index = next_index

    def set_forward_factor(self, factor: float):
        """Set forward and backward movement.

        Parameters
        ----------
        factor : float
            Positive values move forward, negative values move back. Should be in the range -1.0 - 1.0.
        """
        self._forward_factor = factor

    def set_rotation_factor(self, factor: float):
        """Set rotation movement.

        Parameters
        ----------
        factor : float
            Positive values rotate right, negative values rotate left. Should be in the range -1.0 - 1.0.
        """
        if self._rotation_factor >= 0 and factor >= self._rotation_factor:
            self._rotation_factor = min(self._rotation_factor + ROTATION_INCREMENT, 1)

        if self._rotation_factor > 0 and factor < 0:
            self._rotation_factor = max(self._rotation_factor - ROTATION_INCREMENT, -1)

        if self._rotation_factor < 0 and factor > 0:
            self._rotation_factor = min(self._rotation_factor + ROTATION_INCREMENT, 1)

        if self._rotation_factor < 0 and factor < self._rotation_factor:
            self._rotation_factor = max(self._rotation_factor - ROTATION_INCREMENT, -1)

    def set_lean(self, lean: float):
        """Set the distance that it should lean left to right.

        Parameters
        ----------
        lean : float
            Positive values lean right, negative values lean left. Should be in the range -1.0 - 1.0.
        """
        self._lean_factor = lean * LEAN_MULTIPLIER

    def set_height_offset(self, height: float):
        """Set the extra distance for the chassis to be off the ground.

        Parameters
        ----------
        height : float
            Should be in the range 0.0-1.0.
        """
        self._height_factor = height * HEIGHT_MULTIPLIER

    def reset_movement(self):
        """Reset rotation and forward factors to zero."""
        self._rotation_factor = 0
        self._forward_factor = 0

    def reset_body_adjustments(self):
        """Reset height offset and lean to zero."""
        self.set_height_offset(0)
        self.set_lean(0)

    def adjust_walking_speed(self, delta: int):
        """Adjust walking speed by a delta value.

        Parameters
        ----------
        delta : int
            The amount to adjust speed by (can be positive or negative).
        """
        if delta > 0:
            self._walking_speed = max(min(self._walking_speed + 1, MAX_WALKING_SPEED), 0)
        else:
            self._walking_speed = min(max(self._walking_speed - 1, 0), MAX_WALKING_SPEED)

    def reset_walking_state(self):
        """Reset the walking state to initial values. Call this when starting a new walking session."""
        self._elapsed = 0.0
        self._start = time.time()
        self.prev_index = 0

    def update_keyframes(self) -> Keyframe:
        """Update the walking cycle keyframes based on elapsed time.

        This method calculates the current position in the walking cycle and updates
        the current keyframe for each leg based on forward movement and rotation factors.

        Returns
        -------
        Tuple[int, float]
            A tuple of (index, ratio) where index is the current walking cycle index
            and ratio is the interpolation ratio between keyframes (0.0-1.0).
        """
        # Calculate elapsed time and current position in walking cycle
        self._elapsed += (time.time() - self._start) * self._walking_speed
        self._elapsed = self._elapsed % len(self._walking_cycle)

        self._start = time.time()
        next_index = math.floor(self._elapsed)
        ratio = self._elapsed - next_index

        if self.prev_index != next_index:
            self._advance_to_next_keyframe(next_index)

        # Get interpolated leg positions and apply to servos
        return self._interpolate_next_keyframe(ratio)

    def _interpolate_next_keyframe(self, ratio: float) -> Keyframe:
        """Get interpolated leg positions for all four legs.

        This method interpolates between previous and current keyframes based on the
        given ratio, applying height and lean adjustments.

        Parameters
        ----------
        ratio : float
            The interpolation ratio between keyframes (0.0-1.0).

        Returns
        -------
        dict
            A dictionary with keys 'front_right', 'rear_left', 'front_left', 'rear_right',
            each containing a Coordinate representing the interpolated position.
        """
        # Front Right
        start_coord = Coordinate(
            self.__previous_keyframe.front_right.x,
            self.__previous_keyframe.front_right.y + self._height_factor,
            self.__previous_keyframe.front_right.z - self._lean_factor,
        )
        end_coord = Coordinate(
            self.__next_keyframe.front_right.x,
            self.__next_keyframe.front_right.y + self._height_factor,
            self.__next_keyframe.front_right.z - self._lean_factor,
        )
        front_right = start_coord.interpolate_to(end_coord, ratio)

        # Rear Left
        start_coord = Coordinate(
            self.__previous_keyframe.rear_left.x,
            self.__previous_keyframe.rear_left.y + self._height_factor,
            self.__previous_keyframe.rear_left.z + self._lean_factor,
        )
        end_coord = Coordinate(
            self.__next_keyframe.rear_left.x,
            self.__next_keyframe.rear_left.y + self._height_factor,
            self.__next_keyframe.rear_left.z + self._lean_factor,
        )
        rear_left = start_coord.interpolate_to(end_coord, ratio)

        # Front Left
        start_coord = Coordinate(
            self.__previous_keyframe.front_left.x,
            self.__previous_keyframe.front_left.y + self._height_factor,
            self.__previous_keyframe.front_left.z + self._lean_factor,
        )
        end_coord = Coordinate(
            self.__next_keyframe.front_left.x,
            self.__next_keyframe.front_left.y + self._height_factor,
            self.__next_keyframe.front_left.z + self._lean_factor,
        )
        front_left = start_coord.interpolate_to(end_coord, ratio)

        # Rear Right
        start_coord = Coordinate(
            self.__previous_keyframe.rear_right.x,
            self.__previous_keyframe.rear_right.y + self._height_factor,
            self.__previous_keyframe.rear_right.z - self._lean_factor,
        )
        end_coord = Coordinate(
            self.__next_keyframe.rear_right.x,
            self.__next_keyframe.rear_right.y + self._height_factor,
            self.__next_keyframe.rear_right.z - self._lean_factor,
        )
        rear_right = start_coord.interpolate_to(end_coord, ratio)

        return Keyframe(front_left=front_left, front_right=front_right, rear_left=rear_left, rear_right=rear_right)
