# Bézier Curve Foot Trajectory Generator (SpotMicro4)

## Overview
This script replaces the discrete 6-point keyframe “box” walking cycle for a single foot with a **smooth Bézier curve** trajectory.  
Each keyframe defines a 3D coordinate `(X, Y, Z)` in millimeters:
- **X** → forward/backward  
- **Y** → up/down (vertical)  
- **Z** → inward/outward (toward/away from the robot center)

By interpolating these six positions using a Bézier curve, we generate a continuous, smooth path that the robot’s foot can follow during a walking step, reducing mechanical jerk and improving realism.

The Y-axis is plotted **vertically**, and inverted so that positive Y values correspond to **downward movement**, matching the robot’s coordinate convention.

---

## Script: `bezier.py`

```python
import numpy as np
import matplotlib.pyplot as plt
import math

# Your 6 keyframes (in mm)
points = np.array([
    [-60, 150, 40],
    [-60, 80, 40],
    [60, 80, 40],
    [60, 150, 40],
    [35, 150, 40],
    [-35, 150, 40],
])

def bezier_curve(points, num=200):
    n = len(points) - 1
    t = np.linspace(0, 1, num)
    curve = np.zeros((num, 3))
    for i in range(n + 1):
        binomial = math.comb(n, i)
        curve += (
            binomial * ((1 - t) ** (n - i)) * (t ** i)
        )[:, None] * points[i]
    return curve

curve = bezier_curve(points)

# Plot with Y as vertical and inverted
fig = plt.figure()
ax = fig.add_subplot(projection='3d')

# Swap Y/Z for visualization so Y is vertical
ax.plot(points[:, 0], points[:, 2], points[:, 1], 'ro--', label='Keyframes')
ax.plot(curve[:, 0], curve[:, 2], curve[:, 1], 'b-', label='Bezier Curve')

ax.set_xlabel('X (forward/backward)')
ax.set_ylabel('Z (outward/inward)')
ax.set_zlabel('Y (up/down)')
ax.invert_zaxis()  # invert Y axis (vertical)
ax.legend()
plt.tight_layout()
plt.savefig("bezier_curve.png", dpi=200)
print("Saved to bezier_curve.png with Y axis inverted (downward positive)")
```

## Output

Running the script:

```bash
python3 src/bezier.py
```

produces: `bezier_curve.png`

This PNG visualizes:

- The original 6 red keyframes connected by dashed lines
- The smooth blue Bézier curve interpolating the same spatial path
- The Y-axis plotted vertically and inverted to reflect the robot's coordinate frame.

![Bezier Curve Visualization](./bezier-curve.png)