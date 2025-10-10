import math

def InverseKinematics(x, y, z):
    """Main Inverse Kinematic function.

    Calculates the angles (deg.) for each servo (foot, leg, shoulder) on a single leg given
    an offset in mm from the shoulder joint to the foot. The axis (x, y, z) are oriented
    so that the X axis is forward/backward, the Y axis is down/up, and the Z is the distance 
    righ/left. For the Z axis, the direction is flipped on the left side so that positive
    is always away from the center.

    Parameters
    ----------
    x : float
        Distance of the foot along the X axis in mm
    y : float
        Distance of the foot along the Y axis in mm
    z : float
        Distance of the foot along the Z axis in mm

    Returns
    -------
    float: Angle (deg) to set the servo controlling the foot
    float: Angle (deg) to set the servo controlling the leg
    float: Angle (deg) to set the servo controlling the shoulder
    """
    
    # Constant lengths in mm
    E = 110.2 # Upper Leg
    F = 125.5 # Foot
    A = 57.5 # Shoulder Offset

    D = math.sqrt(y*y + z*z - A*A)
    G = math.sqrt(x*x + D*D)
    
    # Foot
    phi = math.acos(clamp((G*G - E*E - F*F)/(-2*E*F), -1, 1))

    # Leg
    theta = math.asin(clamp(F*math.sin(phi), -1, 1)/G) - (math.atan(x / y) if y != 0 else 0)

    # shoulder
    omega = math.atan(G / A) + math.atan(z / y)
    
    # Convert radians to degrees
    phi = round(phi / math.pi * 180, 2)
    theta = round(theta / math.pi * 180, 2)
    omega = round(omega / math.pi * 180, 2)
    
    # print(f'{str(phi)} {str(theta)} {str(omega)}    ------  {x} {y} {z}')
    return phi, theta, omega

def interpolate(x1, x2, ratio):
    """Helper function to interpolate between two values.

    Parameters
    ----------
    x1 : float
        Value from which to interpolate
    x2 : float
        Value to which to interpolate
    ratio : float
        Amount to interpolate. Should be in the range of 0.0 - 1.0

    Returns
    -------
    float: Interpolated value
    """
    ratio = max(0.0, min(ratio, 1.0))
    return x1 + (x2 - x1) * ratio

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)