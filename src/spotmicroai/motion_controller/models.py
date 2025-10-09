from adafruit_motor import servo  # type: ignore

class Coordinate:
    """A class the holds 3 values, x, y and z.

    Used to describe a point in 3-Dimensional space

    Attributes:
        x: The value in the X direction
        y: The value in the Y direction
        z: The value in the Z direction
    """
    x: int
    y: int
    z: int

    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z

class Keyframe:
    """A class the holds 2 coordinates, the current and previous positions of the leg 

    Attributes:
        previous: The prior location of the leg
        current: The current location of the leg
    """

    previous: Coordinate
    current: Coordinate

    def __init__(self, previous: Coordinate, current: Coordinate):
        self.previous = previous
        self.current = current

class KeyframeCollection:
    """A class that contains the 4 keyframes, one per leg 

    Attributes:
        rear_left: The left rear leg
        rear_right: The right rear leg
        front_left: The left front leg 
        front_right: The right front leg
    """

    rear_left: Keyframe
    rear_right: Keyframe
    front_left: Keyframe
    front_right: Keyframe

    def __init__(self, rear_left: Keyframe, rear_right: Keyframe, front_left: Keyframe, front_right: Keyframe):
        self.rear_left = rear_left
        self.rear_right = rear_right
        self.front_left = front_left
        self.front_right = front_right

class Instinct:
    """A class defining an instinct 

    Attributes:
        rear_left: The left rear leg
        rear_right: The right rear leg
        front_left: The left front leg 
        front_right: The right front leg
    """

    rear_left: list[float]
    rear_right: list[float]
    front_left: list[float]
    front_right: list[float]

    def __init__(self, rear_left: list[float], rear_right: list[float], front_left: list[float], front_right: list[float]):
        self.rear_left = rear_left
        self.rear_right = rear_right
        self.front_left = front_left
        self.front_right = front_right

class ServoConfigurations:
    """A class with variables that hold the current configurations of the servo.

    Used to track the configurations of a servo

    Attributes:
        channel: The channel number on the PCA9685 connected to the servo
        min_pulse: The minimum pulse width in microseconds
        max_pulse: The maximum pulse width in microseconds
        rest_angle: The value of the resting angle of the servo
    """
    channel: int
    min_pulse: int
    max_pulse: int
    rest_angle: float

    def __init__(self, channel: int, min_pulse: int, max_pulse: int, rest_angle: float):
        self.channel = channel
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        self.rest_angle = rest_angle

class ServoConfigurationsForLimb:
    """A class containing the configurations for the 3 servos in a single limb.

    Used to track the configurations of 3 servos making a single limb

    Attributes:
        shoulder: The shoulder servo
        leg: The leg servo
        foot: The foot servo
    """
    shoulder: ServoConfigurations
    leg: ServoConfigurations
    foot: ServoConfigurations

    def __init__(self, shoulder: ServoConfigurations, leg: ServoConfigurations, foot: ServoConfigurations):
        self.shoulder = shoulder
        self.leg = leg
        self.foot = foot

class ServoConfigurationsCollection:
    """A class containing the configurations for all the 12 servos.

    Used to track the configurations of all servos

    Attributes:
        rear_left: The rear left limb
        rear_right: The rear right limb
        front_left: The front left limb
        front_right: The front right limb
    """
    rear_left: ServoConfigurationsForLimb
    rear_right: ServoConfigurationsForLimb
    front_left: ServoConfigurationsForLimb
    front_right: ServoConfigurationsForLimb

    def __init__(self, rear_left: ServoConfigurationsForLimb, rear_right: ServoConfigurationsForLimb, front_left: ServoConfigurationsForLimb, front_right: ServoConfigurationsForLimb):
        self.rear_left = rear_left
        self.rear_right = rear_right
        self.front_left = front_left
        self.front_right = front_right

class ServoStateForLimb:
    """A class containing the servos in a single limb.

    Used to track the servos that form a single limb

    Attributes:
        shoulder: The shoulder servo
        leg: The leg servo
        foot: The foot servo
    """
    shoulder: servo.Servo
    leg: servo.Servo
    foot: servo.Servo

    def __init__(self, shoulder: servo.Servo, leg: servo.Servo, foot: servo.Servo):
        self.shoulder = shoulder
        self.leg = leg
        self.foot = foot

class ServoStateCollection:
    """A class containing all the 12 servos.

    Used to track all 12 servos

    Attributes:
        rear_left: The rear left limb
        rear_right: The rear right limb
        front_left: The front left limb
        front_right: The front right limb
    """

    rear_left: ServoStateForLimb
    rear_right: ServoStateForLimb
    front_left: ServoStateForLimb
    front_right: ServoStateForLimb

    def __init__(self, rear_left: ServoStateForLimb, rear_right: ServoStateForLimb, front_left: ServoStateForLimb, front_right: ServoStateForLimb):
        self.rear_left = rear_left
        self.rear_right = rear_right
        self.front_left = front_left
        self.front_right = front_right