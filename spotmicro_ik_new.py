#!/usr/bin/env python3
"""
SpotMicro Inverse Kinematics - with servo offset compensation

Uses the measured physical offsets between the shoulder servo (roll) and and the leg servo (pitch)
and computes the angles ω (omega), θ (theta), and φ (phi) for the leg.

Coordinate system:
  +X = forward
  +Y = downward
  +Z = right

Author: corrected and offset-adjusted version
"""

import math
import sys

# ---------------------------------------------------------------------------
# Constants (in mm)
# ---------------------------------------------------------------------------
UPPER_LEG_LENGTH = 110.0  # "femur" length in mm
LOWER_LEG_LENGTH = 130.0  # "tibia" length in mm
SHOULDER_LENGTH = 57.7  # "coxa" length in mm, effective Z offset = 27.5 + 30.2

# One factor that added significant complexity to the calculations is the fact that
# the shoulder servo and the leg servo's axes of ration do not intersect
# The shoulder servo is 10mm higher from the ground and 24.55mm further from the head
X_OFFSET = 24.55
Y_OFFSET = 10.0
Z_OFFSET = 57.7


# ---------------------------------------------------------------------------
def inverse_kinematics_reference(x: float, y: float, z: float):
    """
    Compute joint angles using corrected SpotMicro equations with offset.

    Args:
        x, y, z: target foot position (mm) relative to the shoulder servo

    Returns:
        (omega, theta, phi) in radians
    """

    # --------------------------------------------------------------
    # 1. Translate target into the Leg servos local coordinate system
    # --------------------------------------------------------------
    # Undo servo offset: subtract the physical offset vector
    xp = x - X_OFFSET
    yp = y - Y_OFFSET
    zp = z - Z_OFFSET

    # --------------------------------------------------------------
    # 2. Compute projected distance in YZ plane (hip roll geometry)
    # --------------------------------------------------------------
    # Avoid domain error: Zp^2 + Yp^2 must exceed SHOULDER_LENGTH^2
    yz_sq = zp**2 + yp**2

    if yz_sq < SHOULDER_LENGTH**2:
        raise ValueError(
            f"Target too close: sqrt(Z^2+Y^2)={math.sqrt(yz_sq):.2f} < SHOULDER_LENGTH={SHOULDER_LENGTH}"
        )

    projected_yz = math.sqrt(
        yz_sq - SHOULDER_LENGTH**2
    )  # horizontal projection after removing roll offset

    # --------------------------------------------------------------
    # 3. Distance from the leg servo pivot to target (planar reach)
    # --------------------------------------------------------------
    planar_reach = math.sqrt(projected_yz**2 + xp**2)

    # Range check
    if not (
        abs(UPPER_LEG_LENGTH - LOWER_LEG_LENGTH)
        <= planar_reach
        <= UPPER_LEG_LENGTH + LOWER_LEG_LENGTH
    ):
        raise ValueError(
            f"Target unreachable: Planar Reach={planar_reach:.2f} not in [{abs(UPPER_LEG_LENGTH - LOWER_LEG_LENGTH)}, {UPPER_LEG_LENGTH + LOWER_LEG_LENGTH}]"
        )

    # --------------------------------------------------------------
    # 4. Roll angle ω (about X)
    # --------------------------------------------------------------
    # Base orientation from Y–Z projection
    omega = math.atan2(yp, zp)  # roll to align leg plane
    # Add neutral mechanical offset if you like, e.g. omega += math.radians(90)

    # --------------------------------------------------------------
    # 5. Knee angle φ (between femur and tibia)
    # --------------------------------------------------------------
    cos_phi = (UPPER_LEG_LENGTH**2 + LOWER_LEG_LENGTH**2 - planar_reach**2) / (
        2 * UPPER_LEG_LENGTH * LOWER_LEG_LENGTH
    )

    cos_phi = max(-1.0, min(1.0, cos_phi))
    phi = math.acos(cos_phi)

    # --------------------------------------------------------------
    # 6. Hip pitch angle θ
    # --------------------------------------------------------------
    theta = math.atan2(xp, projected_yz) + math.asin(
        (LOWER_LEG_LENGTH * math.sin(phi)) / planar_reach
    )

    return omega, theta, phi


# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) != 4:
        print("Usage: spotmicro_ik_reference.py <X> <Y> <Z>")
        sys.exit(1)

    x, y, z = map(float, sys.argv[1:])

    try:
        omega, theta, phi = inverse_kinematics_reference(x, y, z)
        print(f"ω (omega): {omega:.6f} rad ({math.degrees(omega):.2f}°)")
        print(f"θ (theta): {theta:.6f} rad ({math.degrees(theta):.2f}°)")
        print(f"φ (phi):   {phi:.6f} rad ({math.degrees(phi):.2f}°)")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
