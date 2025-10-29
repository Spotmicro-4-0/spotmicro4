# SpotMicro Inverse Kinematics - Final Mathematical Formulas

**As implemented and tested - exact formulas without calibration fudging**

---

## System Parameters

```
L₁ = 110 mm    (femur length)
L₂ = 130 mm    (tibia length)
x_off = 28.55 mm    (X offset of hip from shoulder)
y_off = 10.5 mm     (Y offset of hip at natural position)
z_off = 58.49 mm    (Z offset of hip at natural position)
```

## Joint Angle Convention

- **ω = 90°**: Normal standing position (leg pointing straight down)
- **ω = 180°**: Leg pointing straight sideways
- **ω = 0°**: Leg pointing inward (adducted)
- **θ = 0°**: Femur pointing straight down
- **θ = 90°**: Femur pointing straight backward (along X-axis)
- **φ**: Internal knee angle between femur and tibia

---

## Mathematical Formulas

### Step 1: Solve ω (Shoulder Angle)

**Constraint equation:**
$$Z = -y_{off} \cdot \cos(ω) + z_{off} \cdot \sin(ω)$$

**Rewritten as:**
$$Z = R \cdot \sin(ω + φ)$$

where:
$$R = \sqrt{y_{off}^2 + z_{off}^2}$$
$$φ = \arctan2(-y_{off}, z_{off})$$

**Solution:**
$$ω = \arcsin\left(\frac{Z}{R}\right) - φ$$

**Reachability constraint:**
$$|Z| \leq R$$

### Step 2: Compute Hip Position p₂

$$p_{2x} = x_{off}$$
$$p_{2y} = y_{off} \cdot \sin(ω) + z_{off} \cdot \cos(ω)$$
$$p_{2z} = Z \quad \text{(by construction)}$$

### Step 3: Project to 2D Problem

$$\Delta x = X - p_{2x}$$
$$\Delta y = Y - p_{2y}$$
$$d = \sqrt{(\Delta x)^2 + (\Delta y)^2}$$

**Reachability constraint:**
$$|L_1 - L_2| \leq d \leq L_1 + L_2$$

### Step 4: Solve φ (Knee Angle)

**Law of cosines:**
$$\cos(φ) = \frac{L_1^2 + L_2^2 - d^2}{2L_1L_2}$$

**Solution:**
$$φ = \arccos\left(\text{clamp}\left(\frac{L_1^2 + L_2^2 - d^2}{2L_1L_2}, -1, 1\right)\right)$$

### Step 5: Solve θ (Hip Angle)

**Auxiliary angles:**
$$α = \arctan2(\Delta y, \Delta x)$$
$$β = \arccos\left(\text{clamp}\left(\frac{L_1^2 + d^2 - L_2^2}{2L_1d}, -1, 1\right)\right)$$

**Solution (as currently implemented):**
$$θ = \frac{π}{2} - α + β$$

---

## Summary Algorithm

```python
def inverse_kinematics(X, Y, Z):
    # Step 1: Shoulder angle
    R = sqrt(y_off² + z_off²)
    phi = atan2(-y_off, z_off)
    omega = asin(Z/R) - phi
    
    # Step 2: Hip position
    p2x = x_off
    p2y = y_off * sin(omega) + z_off * cos(omega)
    
    # Step 3: 2D projection
    dx = X - p2x
    dy = Y - p2y
    d = sqrt(dx² + dy²)
    
    # Step 4: Knee angle
    phi = acos(clamp((L1² + L2² - d²)/(2*L1*L2), -1, 1))
    
    # Step 5: Hip angle
    alpha = atan2(dy, dx)
    beta = acos(clamp((L1² + d² - L2²)/(2*L1*d), -1, 1))
    theta = π/2 - alpha + beta
    
    return (omega, theta, phi)
```

---

## Notes

- **The θ formula produces values ~6° lower than expected measurements**
- **The 0.105 radian (~6°) offset in the code is a calibration fudge, not a mathematical solution**
- **The underlying geometric relationship for θ may need reconsideration**
- **All other angles (ω and φ) match measurements accurately**
