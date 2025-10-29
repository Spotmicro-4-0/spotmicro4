

# SpotMicro Leg IK with Shoulder Offset — Cheat Sheet

Frame & signs
**X**: forward/back (positive to the back) • **Y**: up/down (positive down) • **Z**: sideways (positive right).
Angles in **radians** unless noted.

**Link lengths**
(L_1=110,\text{mm}) (femur), (L_2=130,\text{mm}) (tibia)

**Shoulder–hip offset at (\omega=0)**
( (x_{\text{off}},y_{\text{off}},z_{\text{off}})=(28.5,58.5,-10),\text{mm})

> Useful constants (for this robot):
> (R=\sqrt{y_{\text{off}}^2+z_{\text{off}}^2}=59.3485,\text{mm})
> (\delta=\operatorname{atan2}(z_{\text{off}},y_{\text{off}})=-0.1693,\text{rad}) (≈(-9.70^\circ))

---

## Table: From foot position ((X,Y,Z)) to joint angles ((\omega,\theta,\phi))

| Step | Quantity                  | Formula                                                                    | Notes                                                   |         |                                                |
| ---: | ------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------- | ------- | ---------------------------------------------- |
|    0 | Z-reach                   | (                                                                          | Z                                                       | \le R)  | Necessary for a solution (ab/adduction reach). |
|    1 | Shoulder **ab/adduction** | (\displaystyle \omega=\arcsin!\left(\tfrac{Z}{R}\right)-\delta)            | Alternate branch: (\omega=\pi-\arcsin(Z/R)-\delta).     |         |                                                |
|    2 | Hip point (p_2)           | (p_{2x}=x_{\text{off}})                                                    |                                                         |         |                                                |
|      |                           | (p_{2y}=y_{\text{off}}\cos\omega - z_{\text{off}}\sin\omega)               |                                                         |         |                                                |
|      |                           | (p_{2z}=Z)                                                                 | By construction, (Z=p_{2z}).                            |         |                                                |
|    3 | Planar deltas             | (\Delta x=X-x_{\text{off}})                                                | Reduce to the (X!!! -! Y) plane.                        |         |                                                |
|      |                           | (\Delta y=Y-p_{2y})                                                        |                                                         |         |                                                |
|    4 | Hip–foot distance         | (\displaystyle d=\sqrt{(\Delta x)^2+(\Delta y)^2})                         | Planar reach: (                                         | L_1-L_2 | \le d\le L_1+L_2).                             |
|    5 | Knee **internal** angle   | (\displaystyle \phi=\arccos!\left(\tfrac{L_1^2+L_2^2-d^2}{2L_1L_2}\right)) | (\phi=\pi) = straight leg.                              |         |                                                |
|    6 | Aux angles                | (\alpha=\atan2(\Delta y,\Delta x))                                         |                                                         |         |                                                |
|      |                           | (\displaystyle \beta=\arccos!\left(\tfrac{L_1^2+d^2-L_2^2}{2L_1 d}\right)) | Clamp (\arccos) args to ([-1,1]).                       |         |                                                |
|    7 | Hip **pitch**             | **(\theta=\alpha-\beta)**                                                  | “Knee-down” (typical). Mirrored: (\theta=\alpha+\beta). |         |                                                |

---

## Step-by-step recipe (plug in (X,Y,Z))

1. **Shoulder**: (\omega=\arcsin(Z/R)-\delta) (pick branch to match your build).
2. **Hip location**: (p_{2y}=y_{\text{off}}\cos\omega - z_{\text{off}}\sin\omega), and (p_{2x}=x_{\text{off}}).
3. **Planar reduction**: (\Delta x=X-x_{\text{off}}), (\Delta y=Y-p_{2y}); then (d=\sqrt{\Delta x^2+\Delta y^2}).
4. **Knee**: (\phi=\arccos!\left(\frac{L_1^2+L_2^2-d^2}{2L_1L_2}\right)).
5. **Hip pitch**: (\alpha=\atan2(\Delta y,\Delta x)), (\beta=\arccos!\left(\frac{L_1^2+d^2-L_2^2}{2L_1 d}\right)); choose **(\theta=\alpha-\beta)** (or (\alpha+\beta)).

---

## Copy‑paste formulas (ASCII)

**Constants (this robot):**

```text
x_off = 28.5
y_off = 58.5
z_off = -10
L1    = 110
L2    = 130
R     = sqrt(y_off**2 + z_off**2)
delta = atan2(z_off, y_off)
```

**Given foot target (X, Y, Z), compute angles (omega, theta, phi):**

```text
# 1) Shoulder ab/adduction
omega = asin(Z / R) - delta
# Alt branch if needed:
# omega = pi - asin(Z / R) - delta

# 2) Hip location p2 after shoulder rotation
p2x = x_off
p2y = y_off*cos(omega) - z_off*sin(omega)
p2z = Z  # by construction, Z = p2z

# 3) Reduce to the X–Y plane
dx = X - x_off
dy = Y - p2y
d  = sqrt(dx*dx + dy*dy)

# 4) Knee angle (internal)
phi = arccos((L1*L1 + L2*L2 - d*d) / (2*L1*L2))

# 5) Hip pitch
alpha = atan2(dy, dx)
beta  = arccos((L1*L1 + d*d - L2*L2) / (2*L1*d))
# Choose elbow configuration:
theta = alpha - beta        # knee-down (typical)
# or
# theta = alpha + beta      # knee-up (mirror)
```

**Reachability checks:**

```text
abs(Z) <= R
abs(L1 - L2) <= d <= (L1 + L2)
```

## Notes & tips

* Use radians internally; convert to degrees at the end if desired.
* Check reachability: Step 0 ((|Z|\le R)) and Step 4 (triangle inequality).
* Numerical robustness: clamp any (\arccos) inputs to ([-1,1]).
* Quick approximation for seeding (\omega): (\omega\approx\arcsin(Z/y_{\text{off}})) or linearized (\omega\approx (Z-z_{\text{off}})/y_{\text{off}}), then recompute exactly.
