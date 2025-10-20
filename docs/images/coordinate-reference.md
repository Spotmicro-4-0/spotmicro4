### Coordinate System and Anatomical Reference

- **Planes:**  
  - **X–Y plane** → *Sagittal plane* (divides left/right motion)  
  - **X–Z plane** → *Transverse plane* (divides upper/lower motion)  
  - **Y–Z plane** → *Coronal plane* (divides front/back motion)

- **Axes:**  
  - **X-axis** → *Sagittal axis* (forward/backward direction)  
  - **Y-axis** → *Longitudinal axis* (up/down direction)  
  - **Z-axis** → *Frontal axis* (right/left direction)

---
### SpotMicroAI Leg Kinematics Reference

| Joint | Symbol | Description | Plane of Rotation | Axis of Rotation | Link / Segment | Length (mm) | Angle Formula | Angle Range (°) | Notes |
|--------|---------|--------------|-------------------|------------------|----------------|--------------|----------------|-----------------|-------|
| **Shoulder** | **ω** | Rotates the entire leg outward or inward (side sweep) | **Y–Z plane** | **X-axis** | – | – | *Direct servo angle* | 0 → 90 | 0° = leg vertical (downward), 90° = leg extended sideways (Z⁺). |
| **Leg** | **θ** | Controls pitch of the leg (forward/backward motion) | **X–Y plane** (local to shoulder) | **Z-axis (local)** | **Upper leg** | **110** | \( \displaystyle \theta = \tan^{-1}\!\left(\frac{X}{D}\right) + \sin^{-1}\!\left(\frac{L_2 \sin(\phi)}{G}\right) \) | 0 → 180 | 0° = vertical leg, 90° = horizontal, 180° = backward fold. |
| **Foot** | **φ** | Controls extension or folding of the lower segment | **Same plane as θ** | **Z-axis (local)** | **Lower leg (foot)** | **138** | \( \displaystyle \phi = \cos^{-1}\!\left(\frac{G^2 - L_1^2 - L_2^2}{-2L_1L_2}\right) \) | 17 → 131 | 17° = fully folded, 131° = fully extended (safe mechanical range). |

---

### Derived and Supporting Parameters

| Symbol | Meaning | Formula | Example / Value |
|---------|----------|----------|-----------------|
| **L₁** | Length of upper leg (shoulder to joint) | – | 110 mm |
| **L₂** | Length of lower leg (joint to foot tip) | – | 138 mm |
| **G** | Distance shoulder → foot tip | \( G = \sqrt{L_1^2 + L_2^2 - 2L_1L_2\cos(\phi)} \) | Varies (≈46 mm @ φ=17°, ≈161 mm @ φ=80°) |
| **D** | Vertical projection distance (shoulder → ground) | \( D = \sqrt{G^2 - X^2} \) | depends on X |
| **X** | Forward/backward foot displacement | input (mm) | e.g., 0–50 mm |
| **Zₛ** | Shoulder separation distance (right to left) | constant | **57 mm** |

---

### Angle Interpretations

| Angle | 0° | 90° | 180° |
|--------|----|-----|------|
| **ω (shoulder)** | Leg vertical | Leg sideways | (not physically reachable) |
| **θ (leg)** | Vertical down | Horizontal forward | Backward/up |
| **φ (foot)** | Fully folded | Mid bend | Fully extended |

---

### Real-World Servo Offset Compensation

The real shoulder servo is not a perfect point joint — its output gear sits offset from the assumed rotation origin. To correctly account for this in kinematics without altering core formulas, a translation offset must be applied.

**Measured physical offsets (from servo body center to hinge point):**
- ΔX = +24 mm (forward)
- ΔY = +10 mm (up)
- ΔZ = +24 mm (inward toward robot body)

This means the actual shoulder pivot is located 24 mm forward, 10 mm higher, and 24 mm inward relative to the nominal servo center used in the simplified IK model.

**Adjustment method:**

1. **Before IK calculation (input correction):**  
   \( \vec{P}_{ideal} = \vec{P}_{foot} - [24, 10, 24] \)

2. **Perform inverse kinematics using existing φ and θ equations.**

3. **After forward kinematics (output correction):**  
   \( \vec{P}_{foot}^{world} = \vec{P}_{calc} + [24, 10, 24] \)

This translation ensures that the physical servo housing dimensions and real pivot position are accurately represented while preserving the mathematical validity of the core IK equations for θ and φ.

