#!/usr/bin/env python3
"""
SpotMicro Inverse Kinematics - with servo offset compensation

Uses the measured physical offsets between Servo1 (hip roll) and Servo2 (hip pitch)
and computes the angles ω (omega), θ (theta), and φ (phi) for a 2-link leg.

Coordinate system:
  +X = forward (into the body)
  +Y = downward
  +Z = right

Author: corrected and offset-adjusted version
"""

import math
import sys

# ---------------------------------------------------------------------------
# Constants (in mm)
# ---------------------------------------------------------------------------
L1 = 110.0  # femur length
L2 = 130.0  # tibia length
COXA_OFFSET = 57.7  # effective Z offset = 27.5 + 30.2
x_off = 24.55
y_off = 10.0
z_off = 57.7  # includes arm half width


# ---------------------------------------------------------------------------
def inverse_kinematics_reference(X, Y, Z):
    """
    Compute joint angles using corrected SpotMicro equations with offset.

    Args:
        X, Y, Z: target foot position (mm) in the global base (Servo1) frame

    Returns:
        (omega, theta, phi) in radians
    """

    # --------------------------------------------------------------
    # 1. Translate target into the Servo2 local coordinate system
    # --------------------------------------------------------------
    # Undo servo offset: subtract the physical offset vector
    Xp = X - x_off
    Yp = Y - y_off
    Zp = Z - z_off

    # --------------------------------------------------------------
    # 2. Compute projected distance in YZ plane (hip roll geometry)
    # --------------------------------------------------------------
    # Avoid domain error: Zp^2 + Yp^2 must exceed COXA_OFFSET^2
    yz_sq = Zp**2 + Yp**2
    if yz_sq < COXA_OFFSET**2:
        raise ValueError(
            f"Target too close: sqrt(Z^2+Y^2)={math.sqrt(yz_sq):.2f} < COXA_OFFSET={COXA_OFFSET}"
        )

    D = math.sqrt(
        yz_sq - COXA_OFFSET**2
    )  # horizontal projection after removing roll offset

    # --------------------------------------------------------------
    # 3. Distance from Servo2 pivot to target (planar reach)
    # --------------------------------------------------------------
    G = math.sqrt(D**2 + Xp**2)

    # Range check
    if not (abs(L1 - L2) <= G <= L1 + L2):
        raise ValueError(
            f"Target unreachable: G={G:.2f} not in [{abs(L1-L2)}, {L1+L2}]"
        )

    # --------------------------------------------------------------
    # 4. Hip roll angle ω (about X)
    # --------------------------------------------------------------
    # Base orientation from Y–Z projection
    omega = math.atan2(Zp, Yp)  # roll to align leg plane
    # Add neutral mechanical offset if you like, e.g. omega += math.radians(90)

    # --------------------------------------------------------------
    # 5. Knee angle φ (between femur and tibia)
    # --------------------------------------------------------------
    cos_phi = (L1**2 + L2**2 - G**2) / (2 * L1 * L2)
    cos_phi = max(-1.0, min(1.0, cos_phi))
    phi = math.acos(cos_phi)

    # --------------------------------------------------------------
    # 6. Hip pitch angle θ
    # --------------------------------------------------------------
    theta = math.atan2(Xp, D) + math.asin((L2 * math.sin(phi)) / G)

    return omega, theta, phi


# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) != 4:
        print("Usage: spotmicro_ik_reference.py <X> <Y> <Z>")
        sys.exit(1)

    X, Y, Z = map(float, sys.argv[1:])

    try:
        omega, theta, phi = inverse_kinematics_reference(X, Y, Z)
        print(f"ω (omega): {omega:.6f} rad ({math.degrees(omega):.2f}°)")
        print(f"θ (theta): {theta:.6f} rad ({math.degrees(theta):.2f}°)")
        print(f"φ (phi):   {phi:.6f} rad ({math.degrees(phi):.2f}°)")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
