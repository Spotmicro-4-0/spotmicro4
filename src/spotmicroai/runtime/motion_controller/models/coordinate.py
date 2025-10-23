"""
This module defines the Coordinate class for representing 3D points.
"""

import math

import spotmicroai.constants as constants
from spotmicroai.logger import Logger

log = Logger().setup_logger('Motion controller')


class Coordinate:
    """A class that holds 3 values: x, y, and z.

    Used to describe a point in 3-dimensional space.

    Attributes:
        x: The value in the X direction (float).
        y: The value in the Y direction (float).
        z: The value in the Z direction (float).
    """

    @staticmethod
    def _clamp(n, minn, maxn):
        """Clamp a value between min and max."""
        return max(min(maxn, n), minn)

    def __init__(self, x: float = 0.0, y: float = 150.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

    def inverse_kinematics(self) -> tuple[float, float, float]:
        """Compute servo angles (foot, leg, shoulder) for this coordinate.
        Always returns safe numeric values — never raises.
        """

        x, y, z = self.x, self.y, self.z

        try:
            # (1) Projected Shoulder Distance
            term = y * y + z * z - constants.SHOULDER_LENGTH * constants.SHOULDER_LENGTH
            if term < 0:
                term = 0.0  # clamp to avoid sqrt of negative
            distance_yz = math.sqrt(term)

            # (2) Total Reach Length
            distance_total = math.sqrt(x * x + distance_yz * distance_yz)
            if distance_total < 1e-6:
                distance_total = 1e-6  # prevent divide-by-zero

            # (3) Shoulder Rotation
            omega = math.atan(distance_total / max(constants.SHOULDER_LENGTH, 1e-6)) + math.atan2(z, y)

            # (4) Knee (Foot) Angle
            num = (
                distance_total * distance_total
                - constants.LEG_LENGTH * constants.LEG_LENGTH
                - constants.FOOT_LENGTH * constants.FOOT_LENGTH
            )
            denom = -2 * constants.LEG_LENGTH * constants.FOOT_LENGTH
            ratio_phi = num / denom if denom != 0 else 0
            ratio_phi = self._clamp(ratio_phi, -1.0, 1.0)
            phi = math.acos(ratio_phi)

            # (5) Hip (Leg) Angle
            ratio_theta = (constants.LEG_LENGTH * math.sin(phi)) / distance_total
            ratio_theta = self._clamp(ratio_theta, -1.0, 1.0)
            theta = math.atan2(x, distance_yz) + math.asin(ratio_theta)

            # Convert radians to degrees
            phi = round(math.degrees(phi), 2)
            theta = round(math.degrees(theta), 2)
            omega = round(math.degrees(omega), 2)

            # Replace NaN/Inf with safe neutral values
            if not all(math.isfinite(a) for a in (phi, theta, omega)):
                return constants.SAFE_NEUTRAL

            return phi, theta, omega

        except Exception as ex:
            # Never raise — robot must stay alive
            if hasattr(self, "log"):
                log.warning(f"IK fallback due to {ex} for ({x}, {y}, {z})")
            return constants.SAFE_NEUTRAL

    def interpolate_to(self, other: 'Coordinate', ratio: float) -> 'Coordinate':
        """Interpolate between this coordinate (from) and another coordinate (to).

        Args:
            other: The target coordinate to interpolate towards.
            ratio: The interpolation ratio (0.0 to 1.0).

        Returns:
            A new Coordinate instance with interpolated values.
        """
        ratio = self._clamp(ratio, 0.0, 1.0)
        x = self.x + (other.x - self.x) * ratio
        y = self.y + (other.y - self.y) * ratio
        z = self.z + (other.z - self.z) * ratio
        return Coordinate(x, y, z)
