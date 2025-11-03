from enum import Enum


class MessageTopic(Enum):
    ABORT = "abort"
    MOTION = "motion"
    GAIT = "gait"
    LCD_SCREEN = "lcd_screen"
    TELEMETRY = "telemetry"
