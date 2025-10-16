from spotmicroai.motion_controller.models.pose import Pose
from spotmicroai.motion_controller.models.servo_angles import ServoAngles
from spotmicroai.utilities.config import Config
from spotmicroai.utilities.singleton import Singleton


class PoseService(metaclass=Singleton):
    """A singleton class containing predefined poses for the robot.

    Attributes:
        poses: A dictionary of pose names to Pose instances.
        current_index: The index of the current pose in the poses dictionary.
    """

    poses: dict[str, Pose]
    current_index: int

    def __init__(self):
        config = Config()
        poses_data = config.motion_controller.poses

        self.poses = {}

        for pose_name, pose_angles in poses_data.items():
            rear_left = ServoAngles(*pose_angles[0])
            rear_right = ServoAngles(*pose_angles[1])
            front_left = ServoAngles(*pose_angles[2])
            front_right = ServoAngles(*pose_angles[3])

            self.poses[pose_name] = Pose(rear_left, rear_right, front_left, front_right)

        self.current_index = 0

    @property
    def current_pose(self) -> Pose:
        """Get the current pose based on the current index."""
        keys = list(self.poses.keys())
        return self.poses[keys[self.current_index]]

    def next(self) -> Pose:
        """Move to the next pose in the sequence, wrapping around if necessary."""
        self.current_index = (self.current_index + 1) % len(self.poses)
        return self.current_pose

    def previous(self) -> Pose:
        """Move to the previous pose in the sequence, wrapping around if necessary."""
        self.current_index = (self.current_index - 1) % len(self.poses)
        return self.current_pose
