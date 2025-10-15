report_template = """
Spotmicro Robot

Servos
    Count: 12
    Leg Offset: {leg_servo_offset} degrees
    Foot Offset: {foot_servo_offset} degrees
    
    Pinout:
        Servo 1                         Servo 2
        Servo 3                         Servo 4
        Servo 5                         Servo 6
        Servo 7                         Servo 8
        Servo 9                         Servo 10
        Servo 11                        Servo 12

Servo Driver 
    Device  1:
        Model: PCA9685
        I2C Address: {pca9685_1_address}
        Reference Clock: {pca9685_1_reference_clock}
        Frequency: {pca9685_1_frequency}
    boards = 1
    i2c = None
    pca9685_1 = None
    pca9685_2 = None

    pca9685_1_address = None
    pca9685_1_reference_clock_speed = None
    pca9685_1_frequency = None
    pca9685_2_address = None
    pca9685_2_reference_clock_speed = None
    pca9685_2_frequency = None
    
    I2C Address 2: {pca9685_2_address}
        
Abort Controller
    GPIO Pin: {abort_controller_gpio_port}

Game Controller
    Type: XBOX 360 Controller
    Device: {remote_controller_device}
    
Mother Board
    Type: Raspberry PI Zero
    Temprature: {temprature}
    Clock Speed: 

Movement
    Gate Frames: 
    Gait Type: {gait}
    Gait Speed: {gait_speed}
    Forward Factor: {forward}
    Rotation Factor: {rotation}
    Lean Factor: {lean}
    Height Factor: {height}

Instinct
    Current Instinct: 


    
    _is_activated = False

    _servos = []
    _is_gait = False
    _current_gait_type = 0
    _keyframes = []
    _instincts = None

    _forward_factor = -0.5
    _max_forward_factor = 0.5
    _rotation_factor = 0.0
    _lean_factor = 0.0
    _height_factor = 1
    _gait_speed = 7
    _event = {}
    _prev_event = {}

    # It is not possible for the feet to close 100%, so the minimum angle that can be achieved is around 45 degrees
    LEG_SERVO_OFFSET = 45
    # This value can vary based on how you install the legs of the robot. This setting assumes the legs are at 60 degrees when parallel to the body
    FOOT_SERVO_OFFSET = 60

    # This represents the number of seconds in which if no activity is detected, the robot shuts down
    INACTIVITY_TIME = 10

    inactivity_counter

    event

servo_rear_shoulder_left = None
    servo_rear_shoulder_left_pca9685 = None
    servo_rear_shoulder_left_channel = None
    servo_rear_shoulder_left_min_pulse = None
    servo_rear_shoulder_left_max_pulse = None
    servo_rear_shoulder_left_rest_angle = None

    servo_rear_leg_left = None
    servo_rear_leg_left_pca9685 = None
    servo_rear_leg_left_channel = None
    servo_rear_leg_left_min_pulse = None
    servo_rear_leg_left_max_pulse = None
    servo_rear_leg_left_rest_angle = None

    servo_rear_feet_left = None
    servo_rear_feet_left_pca9685 = None
    servo_rear_feet_left_channel = None
    servo_rear_feet_left_min_pulse = None
    servo_rear_feet_left_max_pulse = None
    servo_rear_feet_left_rest_angle = None

    servo_rear_shoulder_right = None
    servo_rear_shoulder_right_pca9685 = None
    servo_rear_shoulder_right_channel = None
    servo_rear_shoulder_right_min_pulse = None
    servo_rear_shoulder_right_max_pulse = None
    servo_rear_shoulder_right_rest_angle = None

    servo_rear_leg_right = None
    servo_rear_leg_right_pca9685 = None
    servo_rear_leg_right_channel = None
    servo_rear_leg_right_min_pulse = None
    servo_rear_leg_right_max_pulse = None
    servo_rear_leg_right_rest_angle = None

    servo_rear_feet_right = None
    servo_rear_feet_right_pca9685 = None
    servo_rear_feet_right_channel = None
    servo_rear_feet_right_min_pulse = None
    servo_rear_feet_right_max_pulse = None
    servo_rear_feet_right_rest_angle = None

    servo_front_shoulder_left = None
    servo_front_shoulder_left_pca9685 = None
    servo_front_shoulder_left_channel = None
    servo_front_shoulder_left_min_pulse = None
    servo_front_shoulder_left_max_pulse = None
    servo_front_shoulder_left_rest_angle = None

    servo_front_leg_left = None
    servo_front_leg_left_pca9685 = None
    servo_front_leg_left_channel = None
    servo_front_leg_left_min_pulse = None
    servo_front_leg_left_max_pulse = None
    servo_front_leg_left_rest_angle = None

    servo_front_feet_left = None
    servo_front_feet_left_pca9685 = None
    servo_front_feet_left_channel = None
    servo_front_feet_left_min_pulse = None
    servo_front_feet_left_max_pulse = None
    servo_front_feet_left_rest_angle = None

    servo_front_shoulder_right = None
    servo_front_shoulder_right_pca9685 = None
    servo_front_shoulder_right_channel = None
    servo_front_shoulder_right_min_pulse = None
    servo_front_shoulder_right_max_pulse = None
    servo_front_shoulder_right_rest_angle = None

    servo_front_leg_right = None
    servo_front_leg_right_pca9685 = None
    servo_front_leg_right_channel = None
    servo_front_leg_right_min_pulse = None
    servo_front_leg_right_max_pulse = None
    servo_front_leg_right_rest_angle = None

    servo_front_feet_right = None
    servo_front_feet_right_pca9685 = None
    servo_front_feet_right_channel = None
    servo_front_feet_right_min_pulse = None
    servo_front_feet_right_max_pulse = None
    servo_front_feet_right_rest_angle = None
"""
# clear = lambda: os.system('cls')


def print_report(data):
    # clear()
    print("", flush=True)
    print(
        report_template.format(
            leg_servo_offset=data['leg_servo_offset'],
            foot_servo_offset=data['foot_servo_offset'],
        )
    )
