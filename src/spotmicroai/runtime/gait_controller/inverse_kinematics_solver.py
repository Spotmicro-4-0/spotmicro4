"""
SpotMicro Kinematics Module

Computes joint angles (ω, θ, φ) for SpotMicro legs given target foot positions.
Accounts for physical offsets between shoulder servo and leg servo axes.
"""

import math
import sys
from typing import Dict, Tuple

from spotmicroai.runtime.motion_controller.models.keyframe import Keyframe

# --------------------------------------------------------------------------- #
# Leg Dimensions (in mm)                                                      #
# --------------------------------------------------------------------------- #

UPPER_LEG_LENGTH = 110.0  # "femur" length
LOWER_LEG_LENGTH = 130.0  # "tibia" length
SHOULDER_LENGTH = 57.7  # "coxa" length / effective Z offset

# --------------------------------------------------------------------------- #
# Servo Offsets (in mm)                                                       #
# --------------------------------------------------------------------------- #

# Physical offset between shoulder servo axis and leg servo axis
X_OFFSET = 24.55
Y_OFFSET = 10.0
Z_OFFSET = 57.7


class InverseKinematicsSolver:
    """Inverse kinematics solver and high-level interface for SpotMicro robot.

    Computes joint angles (ω, θ, φ) for each leg given a target foot position.
    Accounts for the physical offset between the shoulder servo and leg servo axes.
    Converts body state (foot positions) into servo angles for all 12 servos.

    Coordinate system:
      +X = forward
      +Y = downward
      +Z = right
    """

    @staticmethod
    def _compute_single_leg_angles(target_x: float, target_y: float, target_z: float) -> Tuple[float, float, float]:
        """Compute joint angles for a single leg (low-level IK math).

        Args:
            target_x: Target foot X position (mm) relative to shoulder servo
            target_y: Target foot Y position (mm) relative to shoulder servo
            target_z: Target foot Z position (mm) relative to shoulder servo

        Returns:
            (omega, theta, phi) in radians
                omega (ω): Roll angle (about X-axis)
                theta (θ): Hip pitch angle
                phi (φ): Knee angle (between femur and tibia)

        Raises:
            ValueError: If target is unreachable or too close to the servo axis
        """
        # Translate target into leg servo's local coordinate system
        xp = target_x - X_OFFSET
        yp = target_y - Y_OFFSET
        zp = target_z - Z_OFFSET

        # Compute projected distance in YZ plane (hip roll geometry)
        yz_sq = zp**2 + yp**2

        if yz_sq < SHOULDER_LENGTH**2:
            raise ValueError(
                f"Target too close: sqrt(Z^2+Y^2)={math.sqrt(yz_sq):.2f} < SHOULDER_LENGTH={SHOULDER_LENGTH}"
            )

        projected_yz = math.sqrt(yz_sq - SHOULDER_LENGTH**2)

        # Distance from leg servo pivot to target (planar reach)
        planar_reach = math.sqrt(projected_yz**2 + xp**2)

        # Range check: target must be reachable by the two-link leg
        if not (abs(UPPER_LEG_LENGTH - LOWER_LEG_LENGTH) <= planar_reach <= UPPER_LEG_LENGTH + LOWER_LEG_LENGTH):
            raise ValueError(
                f"Target unreachable: Planar Reach={planar_reach:.2f} not in "
                f"[{abs(UPPER_LEG_LENGTH - LOWER_LEG_LENGTH)}, {UPPER_LEG_LENGTH + LOWER_LEG_LENGTH}]"
            )

        # Roll angle ω (about X)
        omega = math.atan2(yp, zp)

        # Knee angle φ (between femur and tibia)
        cos_phi = (UPPER_LEG_LENGTH**2 + LOWER_LEG_LENGTH**2 - planar_reach**2) / (
            2 * UPPER_LEG_LENGTH * LOWER_LEG_LENGTH
        )
        cos_phi = max(-1.0, min(1.0, cos_phi))
        phi = math.acos(cos_phi)

        # Hip pitch angle θ
        theta = math.atan2(xp, projected_yz) + math.asin((LOWER_LEG_LENGTH * math.sin(phi)) / planar_reach)

        return omega, theta, phi

    def compute_joint_angles(self, keyframe: Keyframe) -> Dict[str, float]:
        """Compute all servo angles from keyframe foot positions.

        Args:
            keyframe: Keyframe containing foot positions for all four legs

        Returns:
            Dictionary mapping servo names to angles in degrees
        """
        joint_angles = {}

        # Leg mapping: (servo_prefix, keyframe_attribute, scale_factor)
        # scale_factor: 1 for normal, -1 to invert angle
        leg_configs = [
            ("RF", keyframe.front_right, 1),
            ("RB", keyframe.rear_right, 1),
            ("LF", keyframe.front_left, -1),
            ("LB", keyframe.rear_left, -1),
        ]

        for prefix, foot_pos, scale in leg_configs:
            try:
                # Compute IK for this leg (returns omega, theta, phi in radians)
                omega, theta, phi = self._compute_single_leg_angles(foot_pos.x, foot_pos.y, foot_pos.z)

                # Convert to degrees and apply servo scaling
                # Servo naming: {prefix}_1 = shoulder (roll/omega)
                #              {prefix}_2 = leg (pitch/theta)
                #              {prefix}_3 = foot (knee/phi)
                joint_angles[f"{prefix}_1"] = math.degrees(omega) * scale
                joint_angles[f"{prefix}_2"] = math.degrees(theta) * scale
                joint_angles[f"{prefix}_3"] = math.degrees(phi) * scale

            except ValueError as e:
                # Log error but continue with default angles
                print(f"IK error for {prefix}: {e}", file=sys.stderr)
                joint_angles[f"{prefix}_1"] = 0.0
                joint_angles[f"{prefix}_2"] = 0.0
                joint_angles[f"{prefix}_3"] = 0.0

        return joint_angles
