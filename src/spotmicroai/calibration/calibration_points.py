from dataclasses import dataclass

from spotmicroai.servo import JointType


@dataclass
class CalibrationPoint:
    """Represents a calibration point with angle and pulse width."""

    description: str
    physical_angle: int  # The actual angle in degrees IRL
    pulse_width: int | None = None  # Captured pulse width in microseconds


# Foot calibration: Maps physical angles to servo pulse widths
FOOT_CALIBRATION_POINTS = [
    CalibrationPoint("Minimum position (foot inline with leg)", 17),
    CalibrationPoint("Maximum position (foot perpendicular to leg)", 131),
]

# Leg calibration: Maps physical angles to servo pulse widths
# Calibrate at two easily measurable reference points (0° and 90°)
# and infer the target range through linear extrapolation
LEG_CALIBRATION_POINTS = [
    CalibrationPoint("Reference position 1 (leg vertical, 0°)", 0),
    CalibrationPoint("Reference position 2 (leg horizontal, 90°)", 90),
]

# Shoulder calibration: Maps physical angles to servo pulse widths
# Calibrate at two easily measurable reference points (90° and 180°)
# and infer the target range [60°-120°] through linear extrapolation
# Rest position is at 90° (the first reference point)
SHOULDER_CALIBRATION_POINTS = [
    CalibrationPoint("Reference position 1 (shoulder at 90°, also the rest position)", 90),
    CalibrationPoint("Reference position 2 (shoulder at 180°)", 180),
]

# Mapping of joint types to their calibration specifications
CALIBRATION_POINTS = {
    JointType.SHOULDER: SHOULDER_CALIBRATION_POINTS,
    JointType.LEG: LEG_CALIBRATION_POINTS,
    JointType.FOOT: FOOT_CALIBRATION_POINTS,
}
