from __future__ import annotations
import math
from typing import Tuple

from spotmicroai.runtime.motion_controller.models.coordinate import Coordinate
from spotmicroai.runtime.motion_controller.models.keyframe import Keyframe
from spotmicroai.runtime.motion_controller.models.servo_angles import ServoAngles
from spotmicroai.runtime.gait_controller.inverse_kinematics_solver import InverseKinematicsSolver
from spotmicroai.runtime.gait_controller.models import BodyState, SpotMicroNodeConfig, Command, ContactFeet
from spotmicroai.hardware.servo import ServoService

# --------------------------------------------------------------------------- #
# Utility Functions                                                           #
# --------------------------------------------------------------------------- #


SERVO_NAMES: Tuple[str, ...] = (
    "RF_1",
    "RF_2",
    "RF_3",
    "RB_1",
    "RB_2",
    "RB_3",
    "LF_1",
    "LF_2",
    "LF_3",
    "LB_1",
    "LB_2",
    "LB_3",
)


def rotate_about_y(coordinate: Coordinate, angle_rad: float) -> Coordinate:
    """Rotate a cartesian point about the Y axis."""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    x = cos_a * coordinate.x + sin_a * coordinate.z
    z = -sin_a * coordinate.x + cos_a * coordinate.z
    return Coordinate(x=x, y=coordinate.y, z=z)


def lerp_point(a: Coordinate, b: Coordinate, t: float) -> Coordinate:
    """Linear interpolation between two points."""
    return Coordinate(
        x=a.x + (b.x - a.x) * t,
        y=a.y + (b.y - a.y) * t,
        z=a.z + (b.z - a.z) * t,
    )


# --------------------------------------------------------------------------- #
# Kinematics Interface                                                        #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Gait Controller                                                             #
# --------------------------------------------------------------------------- #


class GaitService:
    """Faithful port of the C++ SpotMicroWalkState implementation.

    Computes walking gaits and foot positions based on commanded body velocity.
    """

    def __init__(
        self,
        config: SpotMicroNodeConfig,
        kinematics: InverseKinematicsSolver,
    ) -> None:
        self.cfg = config
        self.kinematics = kinematics
        self.servo_service = ServoService()
        self.write_to_servos = False  # Disabled until explicitly enabled

        self.body_state = BodyState(
            coordinate=Coordinate(0.0, self.cfg.default_stand_height, 0.0),
            angles=ServoAngles(0.0, 0.0, 0.0),
            keyframe=self._neutral_stance(),
        )

        self.ticks = 0
        self.phase_index = 0
        self.subphase_ticks = 0
        self.contact_states = ContactFeet(False, False, False, False)

    def step(self, command: Command) -> BodyState:
        cmd = command.clamped(self.cfg)

        self._update_phase_data()
        new_feet = self._step_gait(self.body_state, cmd, self.cfg, self._neutral_stance())

        if self.cfg.num_phases == 8:
            new_body_pos = self._step_body_shift(self.body_state, self.cfg)
        else:
            new_body_pos = Coordinate(0.0, self.cfg.default_stand_height, 0.0)

        # Update state and publish servo data
        self.body_state = BodyState(
            coordinate=new_body_pos,
            angles=ServoAngles(0.0, 0.0, 0.0),
            keyframe=new_feet,
        )

        joint_angles = self.kinematics.compute_joint_angles(self.body_state.keyframe)

        # Only write to servos if explicitly enabled (prevents conflicts with motion_controller)
        if self.write_to_servos:
            # Apply servo angles to hardware using ServoService helper methods
            # Servo names map to leg positions: {prefix}_{1,2,3} -> {shoulder,leg,foot}
            self.servo_service.set_front_right_servos(
                foot_angle=joint_angles.get("RF_3", 0.0),
                leg_angle=joint_angles.get("RF_2", 0.0),
                shoulder_angle=joint_angles.get("RF_1", 0.0),
            )
            self.servo_service.set_rear_right_servos(
                foot_angle=joint_angles.get("RB_3", 0.0),
                leg_angle=joint_angles.get("RB_2", 0.0),
                shoulder_angle=joint_angles.get("RB_1", 0.0),
            )
            self.servo_service.set_front_left_servos(
                foot_angle=joint_angles.get("LF_3", 0.0),
                leg_angle=joint_angles.get("LF_2", 0.0),
                shoulder_angle=joint_angles.get("LF_1", 0.0),
            )
            self.servo_service.set_rear_left_servos(
                foot_angle=joint_angles.get("LB_3", 0.0),
                leg_angle=joint_angles.get("LB_2", 0.0),
                shoulder_angle=joint_angles.get("LB_1", 0.0),
            )
            self.servo_service.commit()

        self.ticks += 1
        return self.body_state

    # ---------------------- Internal helpers -------------------------------- #

    def _neutral_stance(self) -> Keyframe:
        length = self.cfg.body_length
        width = self.cfg.body_width
        hip = self.cfg.hip_link_length
        f_off = self.cfg.stand_front_x_offset
        b_off = self.cfg.stand_back_x_offset

        return Keyframe(
            front_left=Coordinate(length / 2 + f_off, 0.0, -width / 2 - hip),
            front_right=Coordinate(length / 2 + f_off, 0.0, width / 2 + hip),
            rear_left=Coordinate(-length / 2 + b_off, 0.0, -width / 2 - hip),
            rear_right=Coordinate(-length / 2 + b_off, 0.0, width / 2 + hip),
        )

    def _update_phase_data(self) -> None:
        phase_time = self.ticks % self.cfg.phase_length
        accumulated = 0

        for idx, phase_ticks in enumerate(self.cfg.phase_ticks or []):
            accumulated += phase_ticks
            if phase_time < accumulated:
                self.phase_index = idx
                self.subphase_ticks = phase_time - accumulated + phase_ticks
                break

        self.contact_states = ContactFeet(
            front_left_in_swing=self.cfg.lf_contact_phases[self.phase_index] == 0,
            front_right_in_swing=self.cfg.rf_contact_phases[self.phase_index] == 0,
            rear_left_in_swing=self.cfg.lb_contact_phases[self.phase_index] == 0,
            rear_right_in_swing=self.cfg.rb_contact_phases[self.phase_index] == 0,
        )

    def _step_gait(
        self,
        body_state: BodyState,
        cmd: Command,
        cfg: SpotMicroNodeConfig,
        default_stance: Keyframe,
    ) -> Keyframe:
        new_positions = {}

        for leg_name in ("front_left", "front_right", "rear_left", "rear_right"):
            in_swing = getattr(self.contact_states, f"{leg_name}_in_swing")
            current_pos = getattr(body_state.keyframe, leg_name)
            default_pos = getattr(default_stance, leg_name)

            if in_swing:
                swing_prop = self.subphase_ticks / float(cfg.swing_ticks)
                new_pos = self._swing_leg_controller(current_pos, cmd, cfg, swing_prop, default_pos)
            else:
                new_pos = self._stance_controller(current_pos, cmd, cfg)

            new_positions[leg_name] = new_pos

        return Keyframe(**new_positions)

    def _stance_controller(self, foot: Coordinate, cmd: Command, cfg: SpotMicroNodeConfig) -> Coordinate:
        dt = cfg.dt
        h_tau = cfg.foot_height_time_constant

        delta_x = -cmd.x_vel_cmd * dt
        delta_y = (1.0 / h_tau) * (0.0 - foot.y) * dt
        delta_z = -cmd.y_vel_cmd * dt

        rotated = rotate_about_y(foot, cmd.yaw_rate_cmd * dt)

        return Coordinate(
            x=rotated.x + delta_x,
            y=rotated.y + delta_y,
            z=rotated.z + delta_z,
        )

    def _swing_leg_controller(
        self,
        foot: Coordinate,
        cmd: Command,
        cfg: SpotMicroNodeConfig,
        swing_prop: float,
        default_foot: Coordinate,
    ) -> Coordinate:
        dt = cfg.dt
        swing_prop = max(0.0, min(0.999, swing_prop))

        if swing_prop < 0.5:
            swing_height = (swing_prop / 0.5) * cfg.z_clearance
        else:
            swing_height = cfg.z_clearance * (1.0 - (swing_prop - 0.5) / 0.5)

        stance_ticks = cfg.stance_ticks
        delta_forward = cfg.alpha * stance_ticks * dt * cmd.x_vel_cmd
        delta_side = cfg.alpha * stance_ticks * dt * cmd.y_vel_cmd
        yaw_delta = cfg.beta * stance_ticks * dt * -cmd.yaw_rate_cmd

        touchdown = rotate_about_y(default_foot, yaw_delta)
        touchdown = Coordinate(
            x=touchdown.x + delta_forward,
            y=touchdown.y,
            z=touchdown.z + delta_side,
        )

        remaining = dt * cfg.swing_ticks * (1.0 - swing_prop)
        remaining = max(1e-5, remaining)

        delta = Coordinate(
            x=(touchdown.x - foot.x) / remaining * dt,
            y=(touchdown.y - foot.y) / remaining * dt,
            z=(touchdown.z - foot.z) / remaining * dt,
        )

        new_foot = Coordinate(
            x=foot.x + delta.x,
            y=swing_height,
            z=foot.z + delta.z,
        )
        return new_foot

    def _step_body_shift(
        self,
        body_state: BodyState,
        cfg: SpotMicroNodeConfig,
    ) -> Coordinate:
        shift_phase = cfg.body_shift_phases[self.phase_index]
        shift_prop = self.subphase_ticks / float(cfg.swing_ticks)
        dt = cfg.dt
        remaining = dt * cfg.swing_ticks * (1.0 - shift_prop)
        remaining = max(1e-5, remaining)

        hold_positions = {
            2: (cfg.fwd_body_balance_shift, -cfg.side_body_balance_shift),
            4: (-cfg.back_body_balance_shift, -cfg.side_body_balance_shift),
            6: (cfg.fwd_body_balance_shift, cfg.side_body_balance_shift),
            8: (-cfg.back_body_balance_shift, cfg.side_body_balance_shift),
        }

        if shift_phase in hold_positions:
            x, z = hold_positions[shift_phase]
            return Coordinate(x=x, y=cfg.default_stand_height, z=z)

        # Determine target corner
        if shift_phase == 1:
            end_x, end_z = cfg.fwd_body_balance_shift, -cfg.side_body_balance_shift
        elif shift_phase == 3:
            end_x, end_z = -cfg.back_body_balance_shift, -cfg.side_body_balance_shift
        elif shift_phase == 5:
            end_x, end_z = cfg.fwd_body_balance_shift, cfg.side_body_balance_shift
        elif shift_phase == 7:
            end_x, end_z = -cfg.back_body_balance_shift, cfg.side_body_balance_shift
        else:
            end_x, end_z = 0.0, 0.0

        delta_x = ((end_x - body_state.coordinate.x) / remaining) * dt
        delta_z = ((end_z - body_state.coordinate.z) / remaining) * dt

        return Coordinate(
            x=body_state.coordinate.x + delta_x,
            y=cfg.default_stand_height,
            z=body_state.coordinate.z + delta_z,
        )
