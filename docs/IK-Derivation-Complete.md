# Inverse Kinematics Derivation for SpotMicro 3-DOF Leg with Shoulder Offset

Pure first-principles derivation. All formulas derived from scratch using only geometry and mathematics.

---

## 1. System Setup

### Physical Configuration
We have a 3-DOF leg with:
- **Joint 1 (Shoulder/Coxa)**: Located at origin p₁
- **Joint 2 (Hip/Femur base)**: Located at offset from p₁
- **Joint 3 (Knee/Tibia base)**: Connected to joint 2 via femur (L₁)
- **End effector (Foot)**: Connected to joint 3 via tibia (L₂)

### Coordinate Frame
- **X**: Forward/backward (positive backward)
- **Y**: Vertical (positive downward)
- **Z**: Lateral (positive rightward)

Origin p₁ is at the shoulder joint.

### Rigid Parameters
- **L₁** = 110 mm (femur/upper leg)
- **L₂** = 130 mm (tibia/lower leg)
- **Offset at rest**: When shoulder is at neutral (ω = 0), hip p₂ is at fixed position (28.5, 58.5, -10) relative to p₁

### Joint Angles
- **ω (omega)**: Shoulder rotation angle. Describes hip p₂ position around X-axis
- **θ (theta)**: Hip joint angle. Describes femur orientation in the plane perpendicular to shoulder axis
- **φ (phi)**: Knee joint angle. Internal angle between femur and tibia

---

## 2. Inverse Kinematics Derivation

### Problem Statement
Given a target foot position **t** = (X, Y, Z), find the joint angles (ω, θ, φ).

### Step 1: Derive ω (Shoulder Abduction/Adduction)

#### Physical Setup
The shoulder joint rotates around the X-axis. The hip joint p₂ is located at an offset from p₁. When the shoulder rotates by angle ω, the offset vector rotates in the YZ plane:

**At ω = 0°:**
$$p_2 = (x_{off}, y_{off}, z_{off}) = (28.5, 58.5, -10)$$

**After rotation by ω around X-axis:**
$$p_{2y} = y_{off}\cos(ω) - z_{off}\sin(ω)$$
$$p_{2z} = y_{off}\sin(ω) + z_{off}\cos(ω)$$

#### Deriving the Constraint
The key constraint is that the foot's Z-coordinate must equal the rotated offset's Z-component:
$$Z = y_{off}\sin(ω) + z_{off}\cos(ω)$$

#### Rewriting with Trigonometric Identity
We can rewrite the right-hand side using the sum formula:
$$Z = \sqrt{y_{off}^2 + z_{off}^2} \left[\frac{y_{off}}{\sqrt{y_{off}^2 + z_{off}^2}}\sin(ω) + \frac{z_{off}}{\sqrt{y_{off}^2 + z_{off}^2}}\cos(ω)\right]$$

Let $\sin(\delta) = \frac{z_{off}}{R}$ and $\cos(\delta) = \frac{y_{off}}{R}$:
$$Z = R[\cos(\delta)\sin(ω) + \sin(\delta)\cos(ω)]$$
$$Z = R\sin(ω + \delta)$$

#### Solving for ω
$$\sin(ω + \delta) = \frac{Z}{R}$$
$$ω + \delta = \arcsin\left(\frac{Z}{R}\right)$$

**Therefore:**
$$\boxed{ω = \arcsin\left(\frac{Z}{R}\right) - \delta}$$

#### Reachability Constraint
$$|Z| \le R \quad \Rightarrow \quad |Z| \le 59.35 \text{ mm}$$

---

### Step 2: Compute p₂ (Hip Position After Shoulder Rotation)

Once ω is determined, the hip joint position is:

$$\boxed{p_{2x} = x_{off} = 28.5 \text{ mm}}$$

$$\boxed{p_{2y} = y_{off}\cos(ω) - z_{off}\sin(ω) = 58.5\cos(ω) + 10\sin(ω)}$$

$$\boxed{p_{2z} = Z}$$

(The Z-coordinate equals the target Z by construction.)

---

### Step 3: Reduce to 2D Planar Problem

#### Project to XY Plane
The leg's remaining two joints (hip and knee) operate in the XY plane. We compute the relative position of the target foot from the hip joint:

$$\boxed{\Delta x = X - p_{2x} = X - 28.5}$$

$$\boxed{\Delta y = Y - p_{2y}}$$

#### Hip-to-Foot Distance
$$\boxed{d = \sqrt{(\Delta x)^2 + (\Delta y)^2}}$$

#### Reachability Constraint (2D Triangle Inequality)
For the two-link chain (L₁ and L₂) to reach distance d:
$$|L_1 - L_2| \le d \le L_1 + L_2$$
$$20 \text{ mm} \le d \le 240 \text{ mm}$$

---

### Step 4: Solve φ (Knee Internal Angle)

#### Law of Cosines
The hip joint p₂, end of femur p₃, and foot target t form a triangle with known side lengths L₁, L₂, and d.

Using the law of cosines:
$$d^2 = L_1^2 + L_2^2 - 2L_1L_2\cos(φ)$$

#### Solving for φ
$$\cos(φ) = \frac{L_1^2 + L_2^2 - d^2}{2L_1L_2}$$

$$\boxed{φ = \arccos\left(\frac{L_1^2 + L_2^2 - d^2}{2L_1L_2}\right)}$$

#### Numerical Robustness
Clamp the arccos argument to [-1, 1] to prevent numerical errors:
$$\cos(φ) = \max(-1, \min(1, \cos(φ)))$$

#### Special Cases
- When $φ = 0°$ (π radians): leg is fully extended
- When $φ = 180°$ (0 radians): leg is fully folded back

---

### Step 5: Solve θ (Hip Pitch Angle)

#### Decomposition into Auxiliary Angles
The hip angle is decomposed into two angles that must be combined:

**Angle α**: Direction from hip p₂ to foot t in the XY plane
$$\boxed{\alpha = \arctan2(\Delta y, \Delta x)}$$

**Angle β**: Angle between the femur (L₁) and the line from hip to foot
Using the law of cosines on the same triangle:
$$L_2^2 = L_1^2 + d^2 - 2L_1 d\cos(β)$$

$$\cos(β) = \frac{L_1^2 + d^2 - L_2^2}{2L_1 d}$$

$$\boxed{\beta = \arccos\left(\frac{L_1^2 + d^2 - L_2^2}{2L_1 d}\right)}$$

#### Numerical Robustness
Clamp the arccos argument:
$$\cos(β) = \max(-1, \min(1, \cos(β)))$$

#### Hip Angle (Knee-Down Configuration)
The femur angle is oriented at angle α, and β is the angle between the femur and the hip-to-foot line. In the "knee-down" (typical) configuration:

$$\boxed{\theta = \alpha - \beta}$$

#### Alternative (Knee-Up Configuration)
For an inverted leg geometry:
$$\theta = \alpha + \beta$$

---

## 3. Complete Algorithm

### Input
Target foot position: $(X, Y, Z)$ in mm

### Output
Joint angles: $(ω, θ, φ)$ in radians

### Algorithm Steps

```
1. Compute shoulder angle:
   IF |Z| > R:
      RETURN ERROR: "Z out of reach"
   END IF
   ω = arcsin(Z/R) - δ

2. Compute hip position:
   p₂ₓ = xₒff
   p₂ᵧ = yₒff·cos(ω) - zₒff·sin(ω)

3. Project to 2D plane:
   Δx = X - p₂ₓ
   Δy = Y - p₂ᵧ
   d = √(Δx² + Δy²)

4. Check 2D reachability:
   IF d < |L₁ - L₂| OR d > L₁ + L₂:
      RETURN ERROR: "Target distance unreachable"
   END IF

5. Compute knee angle:
   cos(φ) = clamp((L₁² + L₂² - d²)/(2·L₁·L₂), -1, 1)
   φ = arccos(cos(φ))

6. Compute hip angle:
   α = atan2(Δy, Δx)
   cos(β) = clamp((L₁² + d² - L₂²)/(2·L₁·d), -1, 1)
   β = arccos(cos(β))
   θ = α - β  (knee-down) or α + β (knee-up)

7. RETURN (ω, θ, φ)
```

---

## 4. Numerical Implementation

### Constants
```
L₁ = 110 mm
L₂ = 130 mm
xₒff = 28.5 mm
yₒff = 58.5 mm
zₒff = -10 mm
R = 59.35 mm
δ ≈ -0.1693 rad
```

### Pseudo-code with Clamping

```python
def inverse_kinematics(X, Y, Z):
    # Step 1: Shoulder angle
    if abs(Z) > R:
        raise ValueError(f"Z={Z} unreachable (max: ±{R})")
    omega = asin(Z/R) - delta
    
    # Step 2: Hip position
    p2x = x_off
    p2y = y_off*cos(omega) - z_off*sin(omega)
    
    # Step 3: 2D projection
    dx = X - p2x
    dy = Y - p2y
    d = sqrt(dx² + dy²)
    
    # Step 4: Check reachability
    if d < abs(L1 - L2) or d > L1 + L2:
        raise ValueError(f"d={d} unreachable")
    
    # Step 5: Knee angle
    cos_phi = clamp((L1² + L2² - d²)/(2*L1*L2), -1, 1)
    phi = acos(cos_phi)
    
    # Step 6: Hip angle
    alpha = atan2(dy, dx)
    cos_beta = clamp((L1² + d² - L2²)/(2*L1*d), -1, 1)
    beta = acos(cos_beta)
    theta = alpha - beta
    
    return omega, theta, phi
```

---

## 5. Validation & Examples

### Example 1: Foot Straight Down
**Input**: X=28.5, Y=170, Z=0

Expected: ω ≈ δ (since arcsin(0) = 0)

**Calculation**:
- ω = arcsin(0) - (-0.1693) = 0.1693 rad ≈ 9.70°
- p₂y = 58.5·cos(0.1693) + 10·sin(0.1693) ≈ 58.36 mm
- d ≈ √(0² + (170-58.36)²) ≈ 111.64 mm

### Example 2: Foot Forward and Down
**Input**: X=60, Y=143, Z=50

Expected: ω > δ (positive Z rotates shoulder to the right)

**Calculation**:
- ω = arcsin(50/59.35) - (-0.1693) ≈ 1.017 rad ≈ 58.29°
- p₂y = 58.5·cos(1.017) + 10·sin(1.017) ≈ 38.47 mm
- d ≈ √((60-28.5)² + (143-38.47)²) ≈ 109.47 mm

---

## 6. Reachability Envelope

The workspace is bounded by:

1. **Z-reach** (shoulder abduction/adduction):
   $$-59.35 \text{ mm} \le Z \le 59.35 \text{ mm}$$

2. **XY-reach** (hip and knee in 2D plane):
   $$20 \text{ mm} \le d \le 240 \text{ mm}$$
   where $d = \sqrt{(X-28.5)^2 + (Y-p_{2y})^2}$

3. **Combined constraint**: The workspace is a 3D region bounded by these limits.

---

## 7. Notes on Implementation

- **Use radians** internally; convert to degrees for display if needed
- **Numerical robustness**: Always clamp arccos arguments to [-1, 1]
- **Branch selection**: The formulas assume the "knee-down" configuration; use $\theta = \alpha + \beta$ for alternative geometry
- **Error handling**: Check both Z-reach and 2D distance reachability before computing angles
- **Singularities**: φ approaches 0 or π at the boundaries of reach; behavior at singularities may cause numerical issues

