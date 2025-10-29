#!/usr/bin/env python3
"""
Inverse Kinematics for SpotMicro 3-DOF Leg with Shoulder Offset

Takes target foot position (X, Y, Z) and computes joint angles (omega, theta, phi).
Based on first-principles derivation with shoulder offset constraint.
"""

import math
import sys


# Constants (in mm)
L1 = 110  # femur length
L2 = 130  # tibia length

# Shoulder offset vector (measured at omega=90° - normal standing position)
# At ω=90°: leg points straight down, p2 = (28.55, 10.5, 58.49)
# This IS the natural offset vector for this geometry
x_off = 28.55
y_off = 10.5
z_off = 58.49

# Pre-computed constants will be calculated inside the function


def inverse_kinematics(X, Y, Z):
    """
    Compute joint angles for target foot position.

    Args:
        X: Forward/back coordinate (mm)
        Y: Up/down coordinate (mm, positive downward)
        Z: Sideways coordinate (mm, positive right)

    Returns:
        tuple: (omega, theta, phi) in radians

    Raises:
        ValueError: If target is unreachable
    """

    # ========== Step 1: Solve for omega (shoulder ab/adduction) ==========
    # Convention: ω=90° is normal standing, ω=180° is sideways, ω=0° is inward
    # Hip rotates from natural position by (ω - 90°) around X-axis
    # At natural ω=90°: p2 = (x_off, y_off, z_off)
    # After rotation: p2z = -y_off*cos(ω) + z_off*sin(ω)

    # Solve: Z = -y_off*cos(ω) + z_off*sin(ω) = R*sin(ω + φ)
    # where R = sqrt(y_off² + z_off²), φ = atan2(-y_off, z_off)

    R = math.sqrt(y_off**2 + z_off**2)
    phi = math.atan2(-y_off, z_off)

    if abs(Z) > R:
        raise ValueError(f"Target Z={Z} is unreachable. Max reach in Z: ±{R:.2f} mm")

    omega = math.asin(Z / R) - phi

    # ========== Step 2: Compute hip position p2 after shoulder rotation ==========
    # Rotation by (ω - 90°) from natural position
    p2x = x_off
    p2y = y_off * math.sin(omega) + z_off * math.cos(omega)  # Updated formula
    # p2z = Z  # By construction (not used further)

    # ========== Step 3: Project to 2D planar problem (X-Y plane) ==========
    dx = X - p2x
    dy = Y - p2y
    d = math.sqrt(dx**2 + dy**2)

    # Check reachability in the 2D plane
    min_reach = abs(L1 - L2)
    max_reach = L1 + L2

    if not (min_reach <= d <= max_reach):
        raise ValueError(
            f"Target distance d={d:.2f} is unreachable. "
            f"Valid range: [{min_reach}, {max_reach}] mm"
        )

    # ========== Step 4: Solve phi (knee internal angle) ==========
    # Law of cosines: d^2 = L1^2 + L2^2 - 2*L1*L2*cos(phi)

    cos_phi = (L1**2 + L2**2 - d**2) / (2 * L1 * L2)
    # Clamp to [-1, 1] for numerical robustness
    cos_phi = max(-1, min(1, cos_phi))
    phi = math.acos(cos_phi)

    # ========== Step 5: Solve theta (hip pitch angle) ==========
    # alpha: angle from hip to foot in the X-Y plane (0 = to the right, pi/2 = down)
    alpha = math.atan2(dy, dx)

    # beta: angle between femur and hip-to-foot line
    cos_beta = (L1**2 + d**2 - L2**2) / (2 * L1 * d)
    cos_beta = max(-1, min(1, cos_beta))
    beta = math.acos(cos_beta)

    # Hip angle in SpotMicro convention (0° = straight down, 90° = straight back)
    # Add small calibration offset based on actual measurements
    theta = math.pi / 2 - alpha + beta + 0.105  # ~6° offset

    return omega, theta, phi


def main():
    """CLI interface: takes X Y Z and outputs omega theta phi."""
    if len(sys.argv) != 4:
        print("Usage: spotmicro_ik.py <X> <Y> <Z>")
        print("  X, Y, Z: target foot position in mm")
        print("  Outputs: omega, theta, phi in radians")
        sys.exit(1)

    try:
        X = float(sys.argv[1])
        Y = float(sys.argv[2])
        Z = float(sys.argv[3])
    except ValueError:
        print("Error: X, Y, Z must be valid numbers")
        sys.exit(1)

    try:
        omega, theta, phi = inverse_kinematics(X, Y, Z)

        # Output in radians
        print(f"omega (ω):  {omega:.6f} rad  ({math.degrees(omega):.2f}°)")
        print(f"theta (θ):  {theta:.6f} rad  ({math.degrees(theta):.2f}°)")
        print(f"phi (φ):    {phi:.6f} rad   ({math.degrees(phi):.2f}°)")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
