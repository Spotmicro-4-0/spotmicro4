from typing import List, Tuple
import math
import time
from spotmicroai.motion_controller.models.coordinate import Coordinate
from spotmicroai.motion_controller.models.keyframe import Keyframe
from spotmicroai.singleton import Singleton
from spotmicroai.utilities.config import Config
from spotmicroai.motion_controller.constants import ROTATION_OFFSET

class KeyframeService(metaclass=Singleton):
    """A class representing a transition from a previous keyframe to a current keyframe.

    Attributes:
        current: The current keyframe (Keyframe).
        previous: The previous keyframe (Keyframe).
    """
    walking_cycle: List[Coordinate] = []
    walking_cycle_length: int = 0
    current: Keyframe
    previous: Keyframe

    def __init__(self):
        self.current = Keyframe()
        self.previous = Keyframe()

        self._forward_factor = 0.0
        self._max_forward_factor = 0.5
        self._rotation_factor = 0.0
        self._lean_factor = 0.0
        self._height_factor = 1.0
        self._walking_speed = 10.0
        
        # Walking state tracking
        self._elapsed = 0.0
        self._start = 0.0
        self._last_index = 0

        if not self.walking_cycle:
            config = Config()
            walking_cycle_data = config.get(Config.MOTION_CONTROLLER_WALKING_CYCLE)
            self.__class__.walking_cycle = [Coordinate(*pos) for pos in walking_cycle_data]
            self.__class__.walking_cycle_length = len(self.walking_cycle)

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
    
    def createNextKeyframe(self):
        """Copy the current keyframe to previous and reset current to default values."""
        self.previous = self.current
        self.current = Keyframe()
    
    def calculate_rotational_movement(self, index: int) -> Tuple[float, float]:
        """Calculate the rotational movement for a given walking cycle index.
        
        Parameters
        ----------
        index : int
            The index in the walking cycle.
            
        Returns
        -------
        Tuple[float, float]
            A tuple of (x_rot, z_rot) representing the rotational offsets.
        """
        # This angle calculation is only used when rotating the bot clockwise or counter clockwise
        angle = 45.0 / 180.0 * math.pi
        x_rot = math.sin(angle) * self._rotation_factor * ROTATION_OFFSET
        z_rot = math.cos(angle) * self._rotation_factor * ROTATION_OFFSET

        angle = (45 + self.walking_cycle[index].x) / 180.0 * math.pi
        x_rot = x_rot - math.sin(angle) * self._rotation_factor * ROTATION_OFFSET
        z_rot = z_rot - math.cos(angle) * self._rotation_factor * ROTATION_OFFSET
        
        return x_rot, z_rot

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
            self._rotation_factor = min(self._rotation_factor + 0.025, 1)

        if self._rotation_factor > 0 and factor < 0:
            self._rotation_factor = max(self._rotation_factor - 0.025, -1)

        if self._rotation_factor < 0 and factor > 0:
            self._rotation_factor = min(self._rotation_factor + 0.025, 1)

        if self._rotation_factor < 0 and factor < self._rotation_factor:
            self._rotation_factor = max(self._rotation_factor - 0.025, -1)

    def set_lean(self, lean: float):
        """Set the distance that it should lean left to right.

        Parameters
        ----------
        lean : float
            Positive values lean right, negative values lean left. Should be in the range -1.0 - 1.0.
        """
        self._lean_factor = lean * 50

    def set_height_offset(self, height: float):
        """Set the extra distance for the chassis to be off the ground.

        Parameters
        ----------
        height : float
            Should be in the range 0.0-1.0.
        """
        self._height_factor = height * 40
    
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
            self._walking_speed = max(min(self._walking_speed + 1, 15), 0)
        else:
            self._walking_speed = min(max(self._walking_speed - 1, 0), 15)
    
    def reset_walking_state(self):
        """Reset the walking state to initial values. Call this when starting a new walking session."""
        self._elapsed = 0.0
        self._start = time.time()
        self._last_index = 0
    
    def update_walking_keyframes(self) -> Tuple[int, float]:
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
        self._elapsed = self._elapsed % self.walking_cycle_length

        self._start = time.time()
        index = math.floor(self._elapsed)
        ratio = self._elapsed - index

        if self._last_index != index:
            # Shift keyframes: current becomes previous, prepare new current
            self.createNextKeyframe()

            # Calculate rotational movement for current index
            x_rot, z_rot = self.calculate_rotational_movement(index)
            
            current_coordinate = self.walking_cycle[index]
            
            # Handle Front-Right and Back-Left legs first
            x = current_coordinate.x * -self._forward_factor + x_rot
            y = current_coordinate.y
            z = current_coordinate.z + z_rot
            self.current.front_right = Coordinate(x, y, z)

            x = current_coordinate.x * -self._forward_factor - x_rot
            y = current_coordinate.y
            z = current_coordinate.z + z_rot
            self.current.rear_left = Coordinate(x, y, z)

            # Handle the other two legs (Front-Left and Back-Right) with phase offset
            adjusted_index = (index + 3) % self.walking_cycle_length
            x_rot, z_rot = self.calculate_rotational_movement(adjusted_index)
            current_coordinate = self.walking_cycle[adjusted_index]
            
            x = current_coordinate.x * -self._forward_factor - x_rot
            y = current_coordinate.y
            z = current_coordinate.z - z_rot
            self.current.front_left = Coordinate(x, y, z)

            x = current_coordinate.x * -self._forward_factor + x_rot
            y = current_coordinate.y
            z = current_coordinate.z - z_rot
            self.current.rear_right = Coordinate(x, y, z)

            self._last_index = index

        return index, ratio
    
    def get_interpolated_leg_positions(self, ratio: float) -> dict:
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
        positions = {}
        
        # Front Right
        start_coord = Coordinate(
            self.previous.front_right.x, 
            self.previous.front_right.y + self._height_factor, 
            self.previous.front_right.z - self._lean_factor
        )
        end_coord = Coordinate(
            self.current.front_right.x, 
            self.current.front_right.y + self._height_factor, 
            self.current.front_right.z - self._lean_factor
        )
        positions['front_right'] = start_coord.interpolate_to(end_coord, ratio)

        # Rear Left
        start_coord = Coordinate(
            self.previous.rear_left.x, 
            self.previous.rear_left.y + self._height_factor, 
            self.previous.rear_left.z + self._lean_factor
        )
        end_coord = Coordinate(
            self.current.rear_left.x, 
            self.current.rear_left.y + self._height_factor, 
            self.current.rear_left.z + self._lean_factor
        )
        positions['rear_left'] = start_coord.interpolate_to(end_coord, ratio)

        # Front Left
        start_coord = Coordinate(
            self.previous.front_left.x, 
            self.previous.front_left.y + self._height_factor, 
            self.previous.front_left.z + self._lean_factor
        )
        end_coord = Coordinate(
            self.current.front_left.x, 
            self.current.front_left.y + self._height_factor, 
            self.current.front_left.z + self._lean_factor
        )
        positions['front_left'] = start_coord.interpolate_to(end_coord, ratio)

        # Rear Right
        start_coord = Coordinate(
            self.previous.rear_right.x, 
            self.previous.rear_right.y + self._height_factor, 
            self.previous.rear_right.z - self._lean_factor
        )
        end_coord = Coordinate(
            self.current.rear_right.x, 
            self.current.rear_right.y + self._height_factor, 
            self.current.rear_right.z - self._lean_factor
        )
        positions['rear_right'] = start_coord.interpolate_to(end_coord, ratio)
        
        return positions