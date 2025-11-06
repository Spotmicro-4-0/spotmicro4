# utils.py
"""
Mathematical utilities and data structures for SpotMicro kinematics.

Implements homogeneous transform utilities, leg coordinate transforms,
and inverse kinematics solvers.
"""

from math import cos, sin

import numpy as np

# ---------------------------------------------------------------------------
# Homogeneous transform helpers
# ---------------------------------------------------------------------------


def _rotate_x(theta: float) -> np.ndarray:
    """Rotation about X-axis."""
    return np.array(
        [
            [1, 0, 0, 0],
            [0, cos(theta), -sin(theta), 0],
            [0, sin(theta), cos(theta), 0],
            [0, 0, 0, 1],
        ]
    )


def _rotate_y(theta: float) -> np.ndarray:
    """Rotation about Y-axis."""
    return np.array(
        [
            [cos(theta), 0, sin(theta), 0],
            [0, 1, 0, 0],
            [-sin(theta), 0, cos(theta), 0],
            [0, 0, 0, 1],
        ]
    )


def _rotate_z(theta: float) -> np.ndarray:
    """Rotation about Z-axis."""
    return np.array(
        [
            [cos(theta), -sin(theta), 0, 0],
            [sin(theta), cos(theta), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )


def rotate_xyz(x_ang: float, y_ang: float, z_ang: float) -> np.ndarray:
    """
    Combines rotations about X, Y, and Z axes sequentially.
    Returns a 4x4 homogeneous transformation matrix.

    Each rotation is post-multiplied (applied on the right).
    """
    # Build identity, then apply rotations in order X, Y, Z
    result = np.eye(4)
    result = result @ _rotate_x(x_ang)
    result = result @ _rotate_y(y_ang)
    result = result @ _rotate_z(z_ang)
    return result


def translate_xyz(x: float, y: float, z: float) -> np.ndarray:
    """
    Creates a homogeneous transformation matrix for translation.
    Translates by the given x, y, z offsets.
    """
    return np.array(
        [
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1],
        ]
    )


def inverse(transform: np.ndarray) -> np.ndarray:
    """
    Computes the inverse of a homogeneous transformation matrix.
    Transposes the rotation matrix and adjusts the translation vector accordingly.
    """
    rotation_matrix = transform[0:3, 0:3]
    translation_vector = transform[0:3, 3]
    inverse_transform = np.eye(4)
    inverse_transform[0:3, 0:3] = rotation_matrix.T
    inverse_transform[0:3, 3] = -rotation_matrix.T @ translation_vector
    return inverse_transform
