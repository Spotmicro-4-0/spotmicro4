### Servo Calibration Guide (Generic Procedure)

This guide explains how to calibrate any hobby servo motor for precise angle control using the Adafruit `servo.Servo()` class. It provides a step-by-step process for determining pulse width limits, mapping them to physical angles, and configuring your code. Example values are provided for reference.

---

### 1. Measure Physical Angle and Pulse Width

Start by moving your servo through its full *safe* range of motion. Use an angle measurement tool (or digital inclinometer) to determine the physical angles corresponding to the minimum and maximum commandable positions.

Record the PWM pulse width values (in microseconds) reported at each position.

| Example Physical Position | Example Angle (°) | Example Pulse (µs) |
|----------------------------|------------------|--------------------|
| Backward limit | -20 | 1463 |
| Vertical (neutral) | 0 | 1611 |
| Forward limit | +110 | 2441 |

> Note: Your angles and pulse widths will differ depending on servo model, linkage geometry, and mechanical constraints.

---

### 2. Determine the Physical Span

Compute the total physical span of motion:

\[ \text{span} = \theta_{max} - \theta_{min} \]

In the example above:

\[ 110 - (-20) = 130° \]

This span will be used as the servo’s `actuation_range`.

---

### 3. Configure the Adafruit Servo Object

The Adafruit `servo.Servo()` object maps angles linearly between two pulse widths:
- `min_pulse` → PWM width at **0°**
- `max_pulse` → PWM width at **actuation_range°**
- `actuation_range` → total logical angle range (degrees)

Example configuration:

```python
s = servo.Servo(
    board.get_channel(config.channel),
    min_pulse=1463,   # example minimum pulse width (µs)
    max_pulse=2441,   # example maximum pulse width (µs)
    actuation_range=130,  # example total range (°)
)
```

---

### 4. Verify the Mapping

Command a few known angles and check their physical positions:

| Example Command | Expected Physical Angle |
|------------------|-------------------------|
| `s.angle = 0` | -20° (backward limit) |
| `s.angle = 20` | 0° (vertical) |
| `s.angle = 130` | +110° (forward limit) |

Adjust `min_pulse` and `max_pulse` slightly if necessary to align the servo precisely with your physical endpoints.

---

### 5. Notes for Safe Calibration
- Always disconnect load-bearing linkages during calibration to avoid stress on servo arms.
- Do **not** exceed your servo’s safe physical limits — mechanical stalls can damage gears.
- Some servos exhibit non-linear behavior near extremes; perform fine-tuning near mid-range for best accuracy.
- Repeat this procedure for each servo individually, as tolerances vary between units.

---

By following this procedure, any hobbyist or developer can accurately calibrate servo limits for use in robotic legs, arms, or other motion-control projects, ensuring smooth, predictable movement across the servo’s safe range.