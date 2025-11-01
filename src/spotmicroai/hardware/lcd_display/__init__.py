"""
LCD display module for SpotMicroAI.
"""

from .i2c_device import I2cDevice
from .lcd_16x2 import Lcd16x2

__all__ = ['I2cDevice', 'Lcd16x2']
