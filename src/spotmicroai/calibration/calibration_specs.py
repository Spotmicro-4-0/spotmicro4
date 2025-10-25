"""Servo calibration specifications for different joint types."""

# Foot calibration: Maps physical angles to servo pulse widths
FOOT_CALIBRATION = {
    "joint_type": "foot",
    "points": [
        {
            "description": "Minimum position (foot inline with leg)",
            "physical_angle": 17.0,
        },
        {
            "description": "Maximum position (foot perpendicular to leg)",
            "physical_angle": 131.0,
        },
    ],
    "target_min_angle": 17.0,
    "target_max_angle": 131.0,
    "rest_angle": 17.0,
}

# Leg calibration: Maps physical angles to servo pulse widths
# Calibrate at two easily measurable reference points (0° and 90°)
# and infer the target range through linear extrapolation
LEG_CALIBRATION = {
    "joint_type": "leg",
    "points": [
        {
            "description": "Reference position 1 (leg vertical, 0°)",
            "physical_angle": 0.0,
        },
        {
            "description": "Reference position 2 (leg horizontal, 90°)",
            "physical_angle": 90.0,
        },
    ],
    "target_min_angle": -20.0,
    "target_max_angle": 110.0,
    "rest_angle": 90.0,
}

# Shoulder calibration: Maps physical angles to servo pulse widths
# Calibrate at two easily measurable reference points (90° and 180°)
# and infer the target range [60°-120°] through linear extrapolation
# Rest position is at 90° (the first reference point)
SHOULDER_CALIBRATION = {
    "joint_type": "shoulder",
    "points": [
        {
            "description": "Reference position 1 (shoulder at 90°, also the rest position)",
            "physical_angle": 90.0,
        },
        {
            "description": "Reference position 2 (shoulder at 180°)",
            "physical_angle": 180.0,
        },
    ],
    "target_min_angle": 60.0,
    "target_max_angle": 120.0,
    "rest_angle": 90.0,
}

# Mapping of joint types to their calibration specifications
CALIBRATION_SPECS = {
    "foot": FOOT_CALIBRATION,
    "leg": LEG_CALIBRATION,
    "shoulder": SHOULDER_CALIBRATION,
}
