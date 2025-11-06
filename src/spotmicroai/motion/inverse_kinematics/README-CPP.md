# SpotMicroKinematics Methods Actually Used in C++ Flow

Looking at the C++ code, here are the **actual methods called** in the real flow:

## 1. **Constructor** (spot_micro_motion_cmd.cpp, line 33)

```cpp
sm_ = smk::SpotMicroKinematics(0.0f, 0.0f, 0.0f, smnc_.smc);
```

Creates the single kinematics instance with zero body position/angles and config.

## 2. **`setBodyState()`** (spot_micro_motion_cmd.cpp, line 43)

```cpp
sm_.setBodyState(body_state_cmd_);
```

Initial setup in constructor. This method:

- Sets `x_`, `y_`, `z_` (body position)
- Sets `phi_`, `theta_`, `psi_` (body angles)
- **Calls `setFeetPosGlobalCoordinates()`** to solve inverse kinematics for all 4 legs

## 3. **`setBodyState()` again** (spot_micro_motion_cmd.cpp, line 335)

```cpp
void SpotMicroMotionCmd::setServoCommandMessageData() {
  sm_.setBodyState(body_state_cmd_);  // ← THE KEY METHOD
  LegsJointAngles joint_angs = sm_.getLegsJointAngles();
  // ... extract angles to servo_cmds_rad_ ...
}
```

**This is called every loop cycle** and is where the magic happens.

## 4. **`getLegsJointAngles()`** (spot_micro_motion_cmd.cpp, line 336)

```cpp
LegsJointAngles joint_angs = sm_.getLegsJointAngles();
```

Retrieves the joint angles that were just solved by `setBodyState()`.

## The Deep Call Stack

When `setBodyState()` is called, here's what actually happens in **spot_micro_kinematics.cpp**:

```cpp
void SpotMicroKinematics::setBodyState(const BodyState& body_state) {
  x_ = body_state.xyz_pos.x;
  y_ = body_state.xyz_pos.y;
  z_ = body_state.xyz_pos.z;

  phi_ = body_state.euler_angs.phi;
  theta_ = body_state.euler_angs.theta;
  psi_ = body_state.euler_angs.psi;

  // ↓ THIS calls the real solver
  setFeetPosGlobalCoordinates(body_state.leg_feet_pos);
}
```

Then `setFeetPosGlobalCoordinates()` does:

```cpp
void SpotMicroKinematics::setFeetPosGlobalCoordinates(
    const LegsFootPos& four_legs_foot_pos) {

  Matrix4f ht_body = getBodyHt();  // Get body transform matrix

  // Create 4 leg starting transforms
  Matrix4f ht_rb = ht_body * htLegRightBack(...);
  Matrix4f ht_rf = ht_body * htLegRightFront(...);
  Matrix4f ht_lf = ht_body * htLegLeftFront(...);
  Matrix4f ht_lb = ht_body * htLegLeftBack(...);

  // ↓ Call each leg's IK solver
  right_back_leg_.setFootPosGlobalCoordinates(four_legs_foot_pos.right_back, ht_rb);
  right_front_leg_.setFootPosGlobalCoordinates(four_legs_foot_pos.right_front, ht_rf);
  left_front_leg_.setFootPosGlobalCoordinates(four_legs_foot_pos.left_front, ht_lf);
  left_back_leg_.setFootPosGlobalCoordinates(four_legs_foot_pos.left_back, ht_lb);
}
```

Each leg's `setFootPosGlobalCoordinates()` **(in spot_micro_leg.cpp)** then:

```cpp
void SpotMicroLeg::setFootPosGlobalCoordinates(const Point& point,
                                               const Matrix4f& ht_leg_start) {
  // Transform global foot position to leg's local coordinates
  Eigen::Vector4f p4_ht_vec(point.x, point.y, point.z, 1.0f);
  p4_ht_vec = homogInverse(ht_leg_start) * p4_ht_vec;

  // ↓ Call inverse kinematics solver
  setFootPosLocalCoordinates(point_local);
}
```

Which calls:

```cpp
void SpotMicroLeg::setFootPosLocalCoordinates(const Point& point) {
  // ↓ THE ACTUAL IK SOLVER
  JointAngles joint_angles = ikine(point, link_lengths_, is_leg_12_);
  setAngles(joint_angles);
}
```

## Summary: Real Methods Called Per Loop

| Method                          | Location            | What It Does                                     |
| ------------------------------- | ------------------- | ------------------------------------------------ |
| `setBodyState()`                | SpotMicroKinematics | **Entry point** - distributes body state to legs |
| `setFeetPosGlobalCoordinates()` | SpotMicroKinematics | Transforms feet positions, calls each leg        |
| `setFootPosGlobalCoordinates()` | SpotMicroLeg (x4)   | Converts global → local coords                   |
| `setFootPosLocalCoordinates()`  | SpotMicroLeg (x4)   | Calls `ikine()` IK solver                        |
| `ikine()`                       | (in utils)          | **Actual inverse kinematics math**               |
| `setAngles()`                   | SpotMicroLeg (x4)   | Stores the solved joint angles                   |
| `getLegsJointAngles()`          | SpotMicroKinematics | Returns all 12 solved angles                     |

**Only 2 public methods are called from `SpotMicroMotionCmd`**: `setBodyState()` and `getLegsJointAngles()`. Everything else is internal delegation.
