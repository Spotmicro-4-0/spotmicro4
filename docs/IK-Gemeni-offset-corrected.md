![alt text](image.png)

# Inverse Kinematics Analysis for SpotMicro Leg (with Shoulder Offset)

This document outlines the derivation of the inverse kinematics equations for a 3-DOF robotic leg, accounting for a physical offset in the shoulder mechanism.

## 1. System Definition

### Coordinate System
- **X-Axis**: Forward/Backward (positive towards the back)
- **Y-Axis**: Up/Down (positive downwards)
- **Z-Axis**: Sideways (positive to the right)

### Link Lengths & Offset
- **L1 (Femur)**: `110 mm`
- **L2 (Tibia)**: `130 mm`
- **Shoulder Offset Vector `v_off`**: The vector from the shoulder rotation axis `p1` to the hip joint `p2` in a zero-rotation state. Based on the provided data (`p2` is at `(28.5, 10, 58.5)` when `ω=90°`), the base offset vector (at `ω=0°`) is `(x_off, y_off, z_off) = (28.5, 58.5, -10)`.

### Joint Angle Definitions
- **ω (omega)**: Shoulder Abduction/Adduction. Rotation at `p1` around the X-axis.
- **θ (theta)**: Hip Flexion/Extension. Rotation at `p2` in the leg's 2D plane.
- **φ (phi)**: Knee Flexion/Extension. The internal angle at `p3` between L1 and L2.

## 2. Inverse Kinematics Derivation with Shoulder Offset

The offset means the position of the hip joint `p2` is a complex function of `ω`, and the problem can no longer be solved with a simple set of analytical formulas. The solution becomes coupled and requires a numerical or iterative approach.

### Hip Joint `p2` Position
The position of `p2` for any angle `ω` is found by rotating the base offset vector `v_off` around the X-axis:
- `p2_x = x_off = 28.5`
- `p2_y = y_off*cos(ω) - z_off*sin(ω) = 58.5*cos(ω) - (-10)*sin(ω) = 58.5*cos(ω) + 10*sin(ω)`
- `p2_z = y_off*sin(ω) + z_off*cos(ω) = 58.5*sin(ω) + (-10)*cos(ω) = 58.5*sin(ω) - 10*cos(ω)`

### The Coupled Equation
The distance from the hip `p2` to the foot `t` is `G`. The squared distance `G²` can be expressed in two ways:
1.  From 3D space: `G² = (x - p2_x)² + (y - p2_y)² + (z - p2_z)²`
2.  From 2D leg kinematics: `G² = L1² + L2² + 2*L1*L2*cos(φ)`

By substituting the equations for `p2` into the first expression, we get a complex trigonometric equation of the form `A*cos(ω) + B*sin(ω) = C`, where `C` itself depends on `G²`.

- `A = 2 * (y*y_off - z*z_off) = 2 * (58.5y + 10z)`
- `B = -2 * (y*z_off + z*y_off) = -2 * (-10y + 58.5z)`
- `C = (x-x_off)² + y² + z² + (y_off² + z_off²) - G²`
  `C = (x-28.5)² + y² + z² + 3522.25 - G²`

This equation links `ω` and `G²` (which depends on `φ`).

## 3. Summary of Final Formulas & Procedure

**Given:** Target `t(x, y, z)`, link lengths `L1=110, L2=130`, and offset parameters.

**Procedure:**

1.  **Find a valid `G²`:**
    The solution requires finding a value for `G²` that satisfies the geometry. This is best done with a numerical search (e.g., a loop or a solver).
    a. Iterate `G²` through its possible range: `(L1-L2)²` to `(L1+L2)²`.
       - `G²_min = (110 - 130)² = 400`
       - `G²_max = (110 + 130)² = 57600`
    b. For each `G²`, calculate the coefficients `A`, `B`, and `C`.
    c. Check if a real solution for `ω` exists by testing if `C² <= A² + B²`. If it does, a valid `G²` has been found. Break the search.

2.  **Calculate Shoulder Angle `ω`:**
    With the valid `G²` and the corresponding `A, B, C`, solve for `ω`:
    `ω = atan2(B, A) - atan2(C, sqrt(A² + B² - C²))`

3.  **Calculate Knee Angle `φ`:**
    With the valid `G²`, the knee angle is straightforward:
    `φ = acos((G² - L1² - L2²) / (2 * L1 * L2))`

4.  **Calculate Hip Angle `θ`:**
    a. First, calculate the final position of `p2` using the solved `ω`.
    b. Determine the coordinates in the leg's 2D plane:
       - `x_leg = x - p2_x`
       - `y_leg = sqrt((y - p2_y)² + (z - p2_z)²) `
    c. Use the 2D IK formula for `θ`:
       `θ = atan2(x_leg, y_leg) + acos((L1² + G² - L2²) / (2 * L1 * G))`
       *(Note: `G` is `sqrt(G²)` found in step 1)*

*This is a significant increase in complexity compared to the non-offset model. The implementation requires a numerical search for `G²` before the final angles can be calculated.*
