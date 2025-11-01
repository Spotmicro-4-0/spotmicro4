from enum import Enum

from spotmicroai.configuration import ServoName


class JointType(Enum):
    """Different types of joints in the robot."""

    FOOT = "foot"
    LEG = "leg"
    SHOULDER = "shoulder"

    @staticmethod
    def from_servo_name(servo_name: ServoName) -> "JointType":
        """
        Determine the JointType from a given ServoName.

        Args:
            servo_name: A ServoName enum value.

        Returns:
            JointType: The corresponding joint type.
        """
        name_str = servo_name.value.lower()

        if "foot" in name_str:
            return JointType.FOOT
        elif "leg" in name_str:
            return JointType.LEG
        elif "shoulder" in name_str:
            return JointType.SHOULDER
        else:
            raise ValueError(f"Unknown joint type in servo name: {servo_name.value}")
