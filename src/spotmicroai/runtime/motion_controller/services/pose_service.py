from spotmicroai import Singleton
from spotmicroai.configuration import ConfigProvider
from spotmicroai.runtime.motion_controller.models.pose import Pose
from spotmicroai.runtime.motion_controller.models.servo_angles import ServoAngles


class PoseService(metaclass=Singleton):
    """A singleton class containing predefined poses for the robot.

    Attributes:
        poses: A dictionary of pose names to Pose instances.
        current_index: The index of the current pose in the poses dictionary.
    """

    poses: dict[str, Pose]
    current_index: int

    def __init__(self):
        _config_provider = ConfigProvider()
        poses_data = _config_provider.get_all_poses()

        self.poses = {}

        for pose_name, pose_angles in poses_data.items():
            rear_left = ServoAngles(*pose_angles[0])
            rear_right = ServoAngles(*pose_angles[1])
            front_left = ServoAngles(*pose_angles[2])
            front_right = ServoAngles(*pose_angles[3])

            self.poses[pose_name] = Pose(front_left, front_right, rear_left, rear_right)

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
