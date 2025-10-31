# SpotMicroAI Servo Calibration Guide

## Overview

This directory contains the servo calibration system for SpotMicroAI. The calibration wizard provides an interactive, step-by-step guide for calibrating each servo joint to ensure precise and consistent movement across the robot.

## Calibration System

The calibration system uses a two-point reference approach to establish accurate servo pulse-width mappings:

1. **Point 1**: Initial reference position
2. **Point 2**: Secondary reference position

These points are used to perform linear extrapolation and determine the full operational range of each servo.

## Joint Types and Specifications

### Shoulder Servos

Shoulder servos control the lateral positioning of the front and rear legs. The calibration range spans from 60° to 120°, with a resting position of 90°.

#### FRONT-LEFT-SHOULDER & REAR-LEFT-SHOULDER
- **Pulse-Angle Relationship**: Increasing pulse width lowers the angle
- **Rest Angle**: 90° (fixed)
- **Operating Range**: 60° – 120°
- **Range Size**: 60°

#### REAR-RIGHT-SHOULDER & FRONT-RIGHT-SHOULDER
- **Pulse-Angle Relationship**: Increasing pulse width increases the angle
- **Rest Angle**: 90° (fixed)
- **Operating Range**: 60° – 120°
- **Range Size**: 60°

### Leg Servos

Leg servos control the knee joint, allowing the legs to flex and extend. Two configurations exist depending on the leg position.

#### Configuration 1 (FRONT-LEFT-LEG & REAR-LEFT-LEG)
- **Pulse-Angle Relationship**: Increasing pulse width increases the angle
- **Rest Angle**: 90° (fixed)
- **Operating Range**: –20° – 110°
- **Range Size**: 130°

#### Configuration 2 (FRONT-RIGHT-LEG & REAR-RIGHT-LEG)
- **Pulse-Angle Relationship**: Increasing pulse width lowers the angle
- **Rest Angle**: 90° (fixed)
- **Operating Range**: –20° – 110°
- **Range Size**: 130°

### Foot Servos

Foot servos control the ankle joint, allowing for vertical foot positioning. The calibration range spans from 17° to 131°, with a resting position of 17°.

#### FRONT-LEFT-FOOT & REAR-LEFT-FOOT
- **Pulse-Angle Relationship**: Increasing pulse width increases the angle
- **Rest Angle**: 17° (fixed)
- **Operating Range**: 17° – 131°
- **Range Size**: 114°

#### FRONT-RIGHT-FOOT & REAR-RIGHT-FOOT
- **Pulse-Angle Relationship**: Increasing pulse width lowers the angle
- **Rest Angle**: 17° (fixed)
- **Operating Range**: 17° – 131°
- **Range Size**: 114°

## Usage

### Interactive Calibration Wizard

To calibrate a single servo, run:

```bash
python calibration_wizard.py <SERVO_ID>
```

Example:
```bash
python calibration_wizard.py front_left_shoulder
```

### Calibrate All Servos

To calibrate all servos sequentially:

```bash
python calibration_wizard.py all
```

### Valid Servo IDs

- `front_left_shoulder`
- `front_right_shoulder`
- `rear_left_shoulder`
- `rear_right_shoulder`
- `front_left_leg`
- `front_right_leg`
- `rear_left_leg`
- `rear_right_leg`
- `front_left_foot`
- `front_right_foot`
- `rear_left_foot`
- `rear_right_foot`

## Calibration Process

1. **Launch the Wizard**: Start the calibration wizard for your target servo
2. **Review Instructions**: Read the joint-specific instructions
3. **Capture Point 1**: Position the servo at the first reference angle and capture
4. **Capture Point 2**: Position the servo at the second reference angle and capture
5. **Confirm Values**: Review the calculated calibration parameters
6. **Save Configuration**: Save the calibration data to persistent storage

## Key Features

- **Interactive CLI Interface**: Real-time visual feedback with pulse width adjustments
- **Fine-Grained Control**: Adjust servo position in 10µs increments
- **Linear Extrapolation**: Accurate calibration across the entire servo range
- **Configuration Persistence**: Calibration data saved to JSON configuration files
- **Servo Recreation**: Servos are automatically recreated with new calibration parameters after saving

## Important Notes

- **Rest Angles Are Fixed**: Each joint type has a fixed rest angle that should not be changed
- **Operating Ranges Are Fixed**: The min and max angle limits for each joint are fixed and should not be modified
- **Physical vs. Local Coordinates**: Calibration uses physical angle coordinates, which are automatically converted to servo local coordinates
- **Two-Point Calibration**: Accurate calibration requires precise positioning at both reference points

## Files

- `calibration_wizard.py` - Interactive calibration wizard
- `servo_controller.py` - Low-level servo control interface
- `calibration_specs.py` - Joint type specifications and calibration constants
- `servo_manual_control.py` - Manual servo testing and debugging tool

## Troubleshooting

**Servo doesn't move to rest position after calibration:**
- Ensure both calibration points were captured at the correct physical angles
- Verify that the servo pulse range is within the hardware's safe operating limits

**Calibration wizard crashes or becomes unresponsive:**
- Check that the servo hardware is properly connected
- Verify the PCA9685 I2C board is accessible
- Ensure no other processes are accessing the servo hardware

**Inaccurate servo movement:**
- Re-run calibration and verify precise positioning at both reference points
- Check for servo hardware issues or mechanical binding