class FootPosition:
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

class FootPositionSet:
    """A class that holds the foot positions for all four legs of the robot.

    Attributes:
        rear_left: The foot position of the left rear leg
        rear_right: The foot position of the right rear leg
        front_left: The foot position of the left front leg
        front_right: The foot position of the right front leg
    """

    rear_left: FootPosition
    rear_right: FootPosition
    front_left: FootPosition
    front_right: FootPosition

    def __init__(self, rear_left: FootPosition, rear_right: FootPosition, front_left: FootPosition, front_right: FootPosition):
        self.rear_left = rear_left
        self.rear_right = rear_right
        self.front_left = front_left
        self.front_right = front_right

class Keyframe:
    """A class the holds 2 coordinates, the current and previous positions of the leg 

    Attributes:
        previous: The prior location of the leg
        current: The current location of the leg
    """

    previous: FootPosition
    current: FootPosition

    def __init__(self, previous: FootPosition, current: FootPosition):
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

class Pose:
    """A class defining an pose 

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