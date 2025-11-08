"""
Servo service for managing and controlling all 12 servos on the SpotMicroAI robot.
Provides high-level interface for setting servo angles, committing changes, and managing poses.
"""

from spotmicroai.singleton import Singleton
from spotmicroai.configuration._config_provider import ConfigProvider, ServoName
from spotmicroai.runtime.motion_controller.models.pose import Pose
from spotmicroai.hardware.servo._servo_factory import ServoFactory
from spotmicroai.hardware.servo.pca9685 import PCA9685
from spotmicroai.hardware.buzzer.buzzer import Buzzer
from spotmicroai.logger import Logger

log = Logger().setup_logger('ServoService')


class ServoService(metaclass=Singleton):
    """Manages and controls all 12 servos using configuration loaded via Config (DotDict-enabled)."""

    def __init__(self):
        self._config_provider = ConfigProvider()
        self._pca9685_board = PCA9685()
        self._buzzer = Buzzer()

        # --- Initialize physical servo objects ---
        self._rear_shoulder_left = ServoFactory.create(ServoName.REAR_SHOULDER_LEFT)
        self._rear_leg_left = ServoFactory.create(ServoName.REAR_LEG_LEFT)
        self._rear_foot_left = ServoFactory.create(ServoName.REAR_FOOT_LEFT)

        self._rear_shoulder_right = ServoFactory.create(ServoName.REAR_SHOULDER_RIGHT)
        self._rear_leg_right = ServoFactory.create(ServoName.REAR_LEG_RIGHT)
        self._rear_foot_right = ServoFactory.create(ServoName.REAR_FOOT_RIGHT)

        self._front_shoulder_left = ServoFactory.create(ServoName.FRONT_SHOULDER_LEFT)
        self._front_leg_left = ServoFactory.create(ServoName.FRONT_LEG_LEFT)
        self._front_foot_left = ServoFactory.create(ServoName.FRONT_FOOT_LEFT)

        self._front_shoulder_right = ServoFactory.create(ServoName.FRONT_SHOULDER_RIGHT)
        self._front_leg_right = ServoFactory.create(ServoName.FRONT_LEG_RIGHT)
        self._front_foot_right = ServoFactory.create(ServoName.FRONT_FOOT_RIGHT)

        # Track if servos have been modified since last commit (dirty flag)
        self._is_dirty = False

        # Initialize all servos to rest position
        self.rest_position()

    def commit(self):
        """Apply all staged servo angles to their respective servo objects by committing each servo individually."""
        if not self._is_dirty:
            # No changes since last commit, skip I²C transaction
            return

        # Skip if PCA9685 board is not activated (e.g., in IDLE state)
        if not self._pca9685_board.is_active():
            log.debug("Skipping commit: PCA9685 board not activated")
            return

        # Collect all servos with names for logging
        servos_with_names = [
            ("rear_shoulder_right", self._rear_shoulder_right),
            ("rear_leg_right", self._rear_leg_right),
            ("rear_foot_right", self._rear_foot_right),
            ("rear_shoulder_left", self._rear_shoulder_left),
            ("rear_leg_left", self._rear_leg_left),
            ("rear_foot_left", self._rear_foot_left),
            ("front_shoulder_left", self._front_shoulder_left),
            ("front_leg_left", self._front_leg_left),
            ("front_foot_left", self._front_foot_left),
            ("front_shoulder_right", self._front_shoulder_right),
            ("front_leg_right", self._front_leg_right),
            ("front_foot_right", self._front_foot_right),
        ]

        log.debug("Committing servos one at a time")
        # Commit each servo individually
        for name, servo_obj in servos_with_names:
            staged_pulse = servo_obj.get_staged_pulse_us()
            channel_idx = servo_obj.channel_index
            log.info(f"Committing {name} (ch{channel_idx}): {staged_pulse:.2f}µs")
            servo_obj.commit_staged()

        self._is_dirty = False

    def clear_staged(self):
        """Reset all staged servo angles to their configured rest angles."""
        self._rear_shoulder_left.stage_angle(self._rear_shoulder_left.rest_angle)
        self._rear_leg_left.stage_angle(self._rear_leg_left.rest_angle)
        self._rear_foot_left.stage_angle(self._rear_foot_left.rest_angle)
        self._rear_shoulder_right.stage_angle(self._rear_shoulder_right.rest_angle)
        self._rear_leg_right.stage_angle(self._rear_leg_right.rest_angle)
        self._rear_foot_right.stage_angle(self._rear_foot_right.rest_angle)
        self._front_shoulder_left.stage_angle(self._front_shoulder_left.rest_angle)
        self._front_leg_left.stage_angle(self._front_leg_left.rest_angle)
        self._front_foot_left.stage_angle(self._front_foot_left.rest_angle)
        self._front_shoulder_right.stage_angle(self._front_shoulder_right.rest_angle)
        self._front_leg_right.stage_angle(self._front_leg_right.rest_angle)
        self._front_foot_right.stage_angle(self._front_foot_right.rest_angle)
        self._is_dirty = True

    def rest_position(self):
        """Return the robot to its rest position."""
        self.clear_staged()
        self.commit()

    def activate_servos(self):
        """Activate the PCA9685 board to enable servo control."""
        self._pca9685_board.activate_board()
        self._buzzer.beep()

    def deactivate_servos(self):
        """Deactivate the PCA9685 board to disable servo control."""
        try:
            self._pca9685_board.deactivate_board()
        except Exception as e:
            log.warning(f"Could not deactivate servos cleanly: {e}")
        self._buzzer.beep()

    def set_pose(self, pose: Pose):
        self._rear_shoulder_left.stage_angle(pose.rear_left.shoulder_angle)
        self._rear_leg_left.stage_angle(pose.rear_left.leg_angle)
        self._rear_foot_left.stage_angle(pose.rear_left.foot_angle)

        self._rear_shoulder_right.stage_angle(pose.rear_right.shoulder_angle)
        self._rear_leg_right.stage_angle(pose.rear_right.leg_angle)
        self._rear_foot_right.stage_angle(pose.rear_right.foot_angle)

        self._front_shoulder_left.stage_angle(pose.front_left.shoulder_angle)
        self._front_leg_left.stage_angle(pose.front_left.leg_angle)
        self._front_foot_left.stage_angle(pose.front_left.foot_angle)

        self._front_shoulder_right.stage_angle(pose.front_right.shoulder_angle)
        self._front_leg_right.stage_angle(pose.front_right.leg_angle)
        self._front_foot_right.stage_angle(pose.front_right.foot_angle)

        self._is_dirty = True

    def set_front_right_servos(self, foot_angle: float, leg_angle: float, shoulder_angle: float):
        """Helper function for setting servo angles for the front right leg.

        Parameters
        ----------
        foot_angle : float
            Servo angle for foot in degrees.
        leg_angle : float
            Servo angle for leg in degrees.
        shoulder_angle : float
            Servo angle for shoulder in degrees.
        """
        self._front_shoulder_right.stage_angle(shoulder_angle)
        self._front_leg_right.stage_angle(leg_angle)
        self._front_foot_right.stage_angle(foot_angle)
        self._is_dirty = True

    def set_front_left_servos(self, foot_angle: float, leg_angle: float, shoulder_angle: float):
        """Helper function for setting servo angles for the front left leg.

        Parameters
        ----------
        foot_angle : float
            Servo angle for foot in degrees.
        leg_angle : float
            Servo angle for leg in degrees.
        shoulder_angle : float
            Servo angle for shoulder in degrees.
        """
        self._front_shoulder_left.stage_angle(shoulder_angle)
        self._front_leg_left.stage_angle(leg_angle)
        self._front_foot_left.stage_angle(foot_angle)
        self._is_dirty = True

    def set_rear_right_servos(self, foot_angle: float, leg_angle: float, shoulder_angle: float):
        """Helper function for setting servo angles for the back right leg.

        Parameters
        ----------
        foot_angle : float
            Servo angle for foot in degrees.
        leg_angle : float
            Servo angle for leg in degrees.
        shoulder_angle : float
            Servo angle for shoulder in degrees.
        """
        self._rear_shoulder_right.stage_angle(shoulder_angle)
        self._rear_leg_right.stage_angle(leg_angle)
        self._rear_foot_right.stage_angle(foot_angle)
        self._is_dirty = True

    def set_rear_left_servos(self, foot_angle: float, leg_angle: float, shoulder_angle: float):
        """Helper function for setting servo angles for the back left leg.

        Parameters
        ----------
        foot_angle : float
            Servo angle for foot in degrees.
        leg_angle : float
            Servo angle for leg in degrees.
        shoulder_angle : float
            Servo angle for shoulder in degrees.
        """
        self._rear_shoulder_left.stage_angle(shoulder_angle)
        self._rear_leg_left.stage_angle(leg_angle)
        self._rear_foot_left.stage_angle(foot_angle)
        self._is_dirty = True

    @property
    def rear_shoulder_left(self) -> float:
        return self._rear_shoulder_left.angle

    @rear_shoulder_left.setter
    def rear_shoulder_left(self, value: float):
        self._rear_shoulder_left.stage_angle(value)
        self._is_dirty = True

    @property
    def rear_leg_left(self) -> float:
        return self._rear_leg_left.angle

    @rear_leg_left.setter
    def rear_leg_left(self, value: float):
        self._rear_leg_left.stage_angle(value)
        self._is_dirty = True

    @property
    def rear_foot_left(self) -> float:
        return self._rear_foot_left.angle

    @rear_foot_left.setter
    def rear_foot_left(self, value: float):
        self._rear_foot_left.stage_angle(value)
        self._is_dirty = True

    @property
    def rear_shoulder_right(self) -> float:
        return self._rear_shoulder_right.angle

    @rear_shoulder_right.setter
    def rear_shoulder_right(self, value: float):
        self._rear_shoulder_right.stage_angle(value)
        self._is_dirty = True

    @property
    def rear_leg_right(self) -> float:
        return self._rear_leg_right.angle

    @rear_leg_right.setter
    def rear_leg_right(self, value: float):
        self._rear_leg_right.stage_angle(value)
        self._is_dirty = True

    @property
    def rear_foot_right(self) -> float:
        return self._rear_foot_right.angle

    @rear_foot_right.setter
    def rear_foot_right(self, value: float):
        self._rear_foot_right.stage_angle(value)
        self._is_dirty = True

    @property
    def front_shoulder_left(self) -> float:
        return self._front_shoulder_left.angle

    @front_shoulder_left.setter
    def front_shoulder_left(self, value: float):
        self._front_shoulder_left.stage_angle(value)
        self._is_dirty = True

    @property
    def front_leg_left(self) -> float:
        return self._front_leg_left.angle

    @front_leg_left.setter
    def front_leg_left(self, value: float):
        self._front_leg_left.stage_angle(value)
        self._is_dirty = True

    @property
    def front_foot_left(self) -> float:
        return self._front_foot_left.angle

    @front_foot_left.setter
    def front_foot_left(self, value: float):
        self._front_foot_left.stage_angle(value)
        self._is_dirty = True

    @property
    def front_shoulder_right(self) -> float:
        return self._front_shoulder_right.angle

    @front_shoulder_right.setter
    def front_shoulder_right(self, value: float):
        self._front_shoulder_right.stage_angle(value)
        self._is_dirty = True

    @property
    def front_leg_right(self) -> float:
        return self._front_leg_right.angle

    @front_leg_right.setter
    def front_leg_right(self, value: float):
        self._front_leg_right.stage_angle(value)
        self._is_dirty = True

    @property
    def front_foot_right(self) -> float:
        return self._front_foot_right.angle

    @front_foot_right.setter
    def front_foot_right(self, value: float):
        self._front_foot_right.stage_angle(value)
        self._is_dirty = True
