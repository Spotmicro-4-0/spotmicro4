# SpotMicro Inverse Kinematics Library

A Python library for computing inverse and forward kinematics for the SpotMicro quadruped robot. This library handles 12-DOF leg kinematics (3 joints × 4 legs) and body pose transformations.

## Architecture

The library follows a hierarchical controller pattern with three main components:

### 1. **SpotmicroKinematics** (Main Robot Controller)
**File:** `spotmicro_kinematics.py`

The high-level robot controller that manages the entire quadruped system.

**Responsibilities:**
- Manages 4 leg instances (`right_back`, `right_front`, `left_front`, `left_back`)
- Tracks body state: position (x, y, z) and orientation (phi, theta, psi Euler angles)
- Coordinates inverse kinematics for the entire robot
- Ensures foot positions remain fixed during body movements

**Key Methods:**
- `set_body_angles(phi, theta, psi)` - Rotate body while keeping feet planted
- `set_body_position(x, y, z)` - Translate body while keeping feet planted
- `set_feet_pos_global_coordinates(foot_positions)` - Command all four foot positions
- `get_legs_joint_angles()` - Retrieve all 12 joint angles
- `get_legs_foot_pos()` - Get current foot positions in world coordinates
- `get_body_state()` - Get complete robot state snapshot
- `get_robot_transforms()` - Get all transformation matrices for visualization

---

### 2. **SpotmicroLeg** (Individual Leg Controller)
**File:** `spotmicro_leg.py`

Controls a single leg of the robot.

**State:**
- `joint_angles` - Current joint positions (th1: hip yaw, th2: hip pitch, th3: knee pitch)
- `link_lengths` - Physical dimensions (l1: hip, l2: upper leg, l3: lower leg)
- `is_leg_12` - Boolean flag affecting IK calculations (True for front/right legs)

**Key Methods:**
- `set_foot_pos_global(point, leg_transform)` - Position foot in world coordinates (uses IK)
- `get_foot_pos_global(leg_transform)` - Forward kinematics (joint angles → foot position)
- `set_angles(joint_angles)` - Directly set joint angles
- `get_transform_0_to_1()`, `get_transform_1_to_3()`, `get_transform_3_to_4()` - Get partial transforms for debugging/visualization

---

### 3. **Utils** (Mathematical Function Library)
**File:** `utils.py`

Pure stateless mathematical utilities for kinematics computations.

**Homogeneous Transforms:**
- `homogeneous_rotation_xyz(x_ang, y_ang, z_ang)` - Create 4×4 rotation matrix
- `homogeneous_translation_xyz(x, y, z)` - Create 4×4 translation matrix
- `homogeneous_inverse(transform)` - Invert a homogeneous transformation

**Leg Coordinate Frames:**
- `ht_leg_right_back(body_length, body_width)` - Body center → right back leg
- `ht_leg_right_front(...)` - Body center → right front leg
- `ht_leg_left_front(...)` - Body center → left front leg
- `ht_leg_left_back(...)` - Body center → left back leg

**Joint Chain Transforms (Denavit-Hartenberg):**
- `homogeneous_transform_joint0_to_1(rot_ang, link_length)` - Hip base → hip yaw
- `homogeneous_transform_joint1_to_2()` - Hip yaw → hip pitch (fixed transform)
- `homogeneous_transform_joint2_to_3(rot_ang, link_length)` - Hip pitch → knee
- `homogeneous_transform_joint3_to_4(rot_ang, link_length)` - Knee → foot
- `homogeneous_transform_joint0_to_4(joint_angles, link_lengths)` - Full leg chain

**Inverse Kinematics:**
- `apply_inverse_kinematics(point, link_lengths, is_leg_12)` - Solve for joint angles given target foot position

---

### 4. **Data Models**
**Files:** `models/*.py`

Plain data structures (using Python dataclasses) representing robot state and configuration.

**Core Types:**
- `Point` - 3D coordinates (x, y, z)
- `JointAngles` - Three joint angles (th1, th2, th3)
- `LinkLengths` - Three link lengths (l1, l2, l3)
- `EulerAngles` - Body orientation (phi, theta, psi)

**Aggregate Types:**
- `LegsJointAngles` - Joint angles for all 4 legs
- `LegsFootPositions` - Foot positions for all 4 legs
- `BodyState` - Complete robot state (body pose + foot positions)
- `SpotmicroConfig` - Robot physical configuration
- `AllRobotRelativeTransforms` - All transformation matrices for visualization
- `LegTransforms` - Per-leg transformation matrices (t01, t13, t34)

---

## Usage Example

```python
from inverse_kinematics import SpotmicroKinematics
from inverse_kinematics.models import SpotmicroConfig

# Define robot dimensions
config = SpotmicroConfig(
    body_length=0.4,        # 40cm body length
    body_width=0.3,         # 30cm body width
    hip_link_length=0.05,   # 5cm hip link
    upper_leg_link_length=0.12,  # 12cm upper leg
    lower_leg_link_length=0.15   # 15cm lower leg
)

# Initialize robot at standing height
kinematics = SpotmicroKinematics(
    x=0.0,    # Body center x position
    y=0.15,   # Body center height (15cm)
    z=0.0,    # Body center z position
    config=config
)

# Move body up by 10cm while keeping feet planted
kinematics.set_body_position(0.0, 0.25, 0.0)

# Rotate body 10 degrees in roll while keeping feet planted
import math
kinematics.set_body_angles(phi=math.radians(10), theta=0.0, psi=0.0)

# Get all joint angles for servo control
joint_angles = kinematics.get_legs_joint_angles()
print(f"Right back leg: {joint_angles.right_back}")
print(f"Right front leg: {joint_angles.right_front}")
print(f"Left front leg: {joint_angles.left_front}")
print(f"Left back leg: {joint_angles.left_back}")

# Get current foot positions
foot_positions = kinematics.get_legs_foot_pos()
print(f"Right back foot: ({foot_positions.right_back.x}, "
      f"{foot_positions.right_back.y}, {foot_positions.right_back.z})")
```

---

## Call Flow

Here's how a typical operation flows through the library:

```
User calls: kinematics.set_body_position(0, 0.25, 0)
    │
    ├─→ Main class saves current foot positions
    │   └─→ get_legs_foot_pos()
    │       └─→ For each leg: leg.get_foot_pos_global()
    │           └─→ Uses utils: homogeneous transforms
    │
    ├─→ Updates internal body position
    │   └─→ self.y = 0.25
    │
    └─→ Recomputes joint angles to maintain foot positions
        └─→ set_feet_pos_global_coordinates(saved_positions)
            └─→ For each leg: leg.set_foot_pos_global()
                ├─→ Uses utils: homogeneous_inverse()
                └─→ Uses utils: apply_inverse_kinematics()
                    └─→ Updates leg.joint_angles
```

---

## Design Benefits

- **Separation of Concerns:** Mathematical operations (utils) are separate from state management (classes)
- **Reusability:** Pure functions can be tested and used independently
- **Modularity:** Components can be modified or replaced without affecting others
- **Type Safety:** Dataclasses provide clear interfaces and IDE autocomplete support
- **Testability:** Stateless functions are easy to unit test

---

## Joint Coordinate System

Each leg has 4 coordinate frames corresponding to joints:

| Joint | Name | Type | Symbol | Function |
|-------|------|------|--------|----------|
| 0 | Hip base | Fixed reference | — | Leg origin (attached to body) |
| 1 | Hip yaw | Revolute | θ₁ | Rotates leg outward/inward |
| 2 | Hip pitch | Revolute | θ₂ | Lifts leg forward/backward |
| 3 | Knee pitch | Revolute | θ₃ | Bends the leg (extends/retracts) |
| 4 | Foot | End-effector | — | Not actuated, endpoint of chain |

---

## Dependencies

- **NumPy** - For matrix operations and numerical computations
- **Python 3.7+** - For dataclass support

---

## Installation

```bash
# Install dependencies
pip install numpy

# Import the library
from inverse_kinematics import SpotmicroKinematics
```

---

## License

See LICENSE file in the repository root.
