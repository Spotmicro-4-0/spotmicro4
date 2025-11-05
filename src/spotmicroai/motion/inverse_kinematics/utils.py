# utils.py
"""
Mathematical utilities and data structures for SpotMicro kinematics.

Implements homogeneous transform utilities, leg coordinate transforms,
and inverse kinematics solvers.
"""

from math import atan2, cos, sin, sqrt, pi

import numpy as np

from .models import JointAngles, LinkLengths, Point

# ---------------------------------------------------------------------------
# Homogeneous transform helpers
# ---------------------------------------------------------------------------


def _homogeneous_rotation_x(theta: float) -> np.ndarray:
    """Rotation about X-axis."""
    return np.array(
        [
            [1, 0, 0, 0],
            [0, cos(theta), -sin(theta), 0],
            [0, sin(theta), cos(theta), 0],
            [0, 0, 0, 1],
        ]
    )


def _homogeneous_rotation_y(theta: float) -> np.ndarray:
    """Rotation about Y-axis."""
    return np.array(
        [
            [cos(theta), 0, sin(theta), 0],
            [0, 1, 0, 0],
            [-sin(theta), 0, cos(theta), 0],
            [0, 0, 0, 1],
        ]
    )


def _homogeneous_rotation_z(theta: float) -> np.ndarray:
    """Rotation about Z-axis."""
    return np.array(
        [
            [cos(theta), -sin(theta), 0, 0],
            [sin(theta), cos(theta), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )


def homogeneous_rotation_xyz(x_ang: float, y_ang: float, z_ang: float) -> np.ndarray:
    """
    Combines rotations about X, Y, and Z axes sequentially.
    Returns a 4x4 homogeneous transformation matrix.
    
    Matches Eigen's AngleAxis rotation order (intrinsic XYZ).
    Each rotation is post-multiplied (applied on the right).
    """
    # Build identity, then apply rotations in order X, Y, Z
    # This matches C++: t.rotate(X).rotate(Y).rotate(Z)
    result = np.eye(4)
    result = result @ _homogeneous_rotation_x(x_ang)
    result = result @ _homogeneous_rotation_y(y_ang)
    result = result @ _homogeneous_rotation_z(z_ang)
    return result


def homogeneous_translation_xyz(x: float, y: float, z: float) -> np.ndarray:
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


def homogeneous_inverse(transform: np.ndarray) -> np.ndarray:
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


# ---------------------------------------------------------------------------
# Leg coordinate system transforms
# ---------------------------------------------------------------------------


def ht_leg_right_back(body_length: float, body_width: float) -> np.ndarray:
    """Homogeneous transform from body center to right-back leg frame."""
    # Rotate 90° about Y-axis
    transform = homogeneous_rotation_xyz(0.0, pi / 2.0, 0.0)

    # Apply translation
    transform[0:3, 3] = np.array([-body_length / 2.0, 0.0, body_width / 2.0])

    return transform


def ht_leg_right_front(body_length: float, body_width: float) -> np.ndarray:
    """htLegRightFront(): center → right-front leg."""
    transform = homogeneous_rotation_xyz(0.0, pi / 2.0, 0.0)
    transform[0:3, 3] = np.array([body_length / 2.0, 0.0, body_width / 2.0])
    return transform


def ht_leg_left_front(body_length: float, body_width: float) -> np.ndarray:
    """htLegLeftFront(): center → left-front leg."""
    transform = homogeneous_rotation_xyz(0.0, -pi / 2.0, 0.0)  # NEGATIVE rotation for left legs
    transform[0:3, 3] = np.array([body_length / 2.0, 0.0, -body_width / 2.0])
    return transform


def ht_leg_left_back(body_length: float, body_width: float) -> np.ndarray:
    """htLegLeftBack(): center → left-back leg."""
    transform = homogeneous_rotation_xyz(0.0, -pi / 2.0, 0.0)  # NEGATIVE rotation for left legs
    transform[0:3, 3] = np.array([-body_length / 2.0, 0.0, -body_width / 2.0])
    return transform


# ---------------------------------------------------------------------------
# Leg joint transforms (Denavit–Hartenberg–like chain)
# ---------------------------------------------------------------------------
def homogeneous_transform_joint0_to_1(rot_ang: float, link_length: float) -> np.ndarray:
    """
    ht0To1()
    Transform from joint 0 to joint 1 (hip yaw → hip pitch).
    
    Matches C++ implementation exactly:
    - Rotation about Z axis by rot_ang
    - Translation: x = -link_length*cos(rot_ang), y = -link_length*sin(rot_ang), z = 0
    """
    transform = homogeneous_rotation_xyz(0.0, 0.0, rot_ang)
    # Explicit translation as per C++ code
    transform[0, 3] = -link_length * cos(rot_ang)
    transform[1, 3] = -link_length * sin(rot_ang)
    # transform[2, 3] remains 0.0
    return transform


# | Joint index | Physical joint          | Type            | Symbol | Function                                        |
# | ----------- | ----------------------- | --------------- | ------ | ----------------------------------------------- |
# | 0           | **Hip base**            | fixed reference | —      | the leg’s origin (attached to body)             |
# | 1           | **Hip yaw**             | revolute        | θ₁     | rotates leg outward/inward around vertical axis |
# | 2           | **Hip pitch**           | revolute        | θ₂     | lifts leg forward/backward                      |
# | 3           | **Knee pitch**          | revolute        | θ₃     | bends the leg (extends/retracts)                |
# | 4           | **Foot (end-effector)** | —               | —      | not actuated, endpoint of chain                 |


def homogeneous_transform_joint1_to_2() -> np.ndarray:
    """
    ht1To2()
    Transform from joint 1 to joint 2 (hip pitch → knee).
    
    Returns the exact 4x4 matrix from C++ implementation.
    This is a fixed coordinate frame transformation.
    """
    ht_1_to_2 = np.array([
        [ 0.0,  0.0, -1.0,  0.0],
        [-1.0,  0.0,  0.0,  0.0],
        [ 0.0,  1.0,  0.0,  0.0],
        [ 0.0,  0.0,  0.0,  1.0]
    ])
    return ht_1_to_2


def homogeneous_transform_joint2_to_3(rot_ang: float, link_length: float) -> np.ndarray:
    """
    ht2To3()
    Transform from joint 2 to joint 3 (knee → shin).
    
    Matches C++ implementation exactly:
    - Rotation about Z axis by rot_ang
    - Translation: x = link_length*cos(rot_ang), y = link_length*sin(rot_ang), z = 0
    """
    transform = homogeneous_rotation_xyz(0.0, 0.0, rot_ang)
    # Explicit translation as per C++ code (POSITIVE signs)
    transform[0, 3] = link_length * cos(rot_ang)
    transform[1, 3] = link_length * sin(rot_ang)
    # transform[2, 3] remains 0.0
    return transform


def homogeneous_transform_joint3_to_4(rot_ang: float, link_length: float) -> np.ndarray:
    """
    ht3To4()
    Transform from joint 3 to joint 4 (shin → foot).
    
    C++ implementation just calls ht2To3(), so this is identical.
    """
    # Same as ht2To3 per C++ code
    return homogeneous_transform_joint2_to_3(rot_ang, link_length)


def homogeneous_transform_joint0_to_4(joint_angles: JointAngles, link_lengths: LinkLengths) -> np.ndarray:
    """
    ht0To4()
    Full homogeneous transform from hip base to foot (end-effector).
    """
    return (
        homogeneous_transform_joint0_to_1(joint_angles.th1, link_lengths.l1)
        @ homogeneous_transform_joint1_to_2()
        @ homogeneous_transform_joint2_to_3(joint_angles.th2, link_lengths.l2)
        @ homogeneous_transform_joint3_to_4(joint_angles.th3, link_lengths.l3)
    )


# ---------------------------------------------------------------------------
# Inverse kinematics solver
# ---------------------------------------------------------------------------


def apply_inverse_kinematics(point: Point, link_lengths: LinkLengths, is_leg_12: bool = True) -> JointAngles:
    """
    Compute inverse kinematics for one leg of SpotMicro.

    Args:
        point: Target foot position (x, y, z) in leg coordinates.
        link_lengths: LinkLengths(l1, l2, l3)
        is_leg_12: True for front legs (1,2); False for back legs (3,4)

    Returns:
        JointAngles(th1, th2, th3)
    """

    x4, y4, z4 = point.x, point.y, point.z
    l1, l2, l3 = link_lengths.l1, link_lengths.l2, link_lengths.l3

    # --- Compute D (law of cosines term)
    d = (x4**2 + y4**2 + z4**2 - l1**2 - l2**2 - l3**2) / (2 * l2 * l3)

    # Clamp D to [-1, 1] for numerical safety
    d = max(min(d, 1.0), -1.0)

    # --- Knee joint angle (ang3)
    if is_leg_12:
        ang3 = atan2(sqrt(1 - d**2), d)
    else:
        ang3 = atan2(-sqrt(1 - d**2), d)

    # --- Hip pitch angle (ang2)
    protected_sqrt_val = x4**2 + y4**2 - l1**2
    if protected_sqrt_val < 0.0:
        protected_sqrt_val = 0.0

    ang2 = atan2(z4, sqrt(protected_sqrt_val)) - atan2(l3 * sin(ang3), l2 + l3 * cos(ang3))

    # --- Hip yaw angle (ang1)
    ang1 = atan2(y4, x4) + atan2(sqrt(protected_sqrt_val), -l1)

    return JointAngles(th1=ang1, th2=ang2, th3=ang3)
