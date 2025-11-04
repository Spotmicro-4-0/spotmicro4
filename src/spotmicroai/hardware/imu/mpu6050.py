"""
MPU6050 Sensor Driver Module

Provides a Python driver for the MPU6050 6-axis IMU (accelerometer + gyroscope).

Features:
- Read accelerometer and gyroscope data
- Read temperature
- I2C interface
- Simple initialization and scaling

Example:
    >>> sensor = MPU6050()
    >>> ax, ay, az, gx, gy, gz, temp = sensor.read()
    >>> print(f"Accel: {ax:.2f}, {ay:.2f}, {az:.2f} g | Gyro: {gx:.2f}, {gy:.2f}, {gz:.2f} °/s | Temp: {temp:.2f} °C")
"""

import time

import smbus2  # type: ignore


class MPU6050:
    """MPU6050 6-axis IMU sensor driver."""

    _ADDR = 0x68  # I2C address

    # Register map (subset)
    _PWR_MGMT_1 = 0x6B
    _SMPLRT_DIV = 0x19
    _CONFIG = 0x1A
    _GYRO_CONFIG = 0x1B
    _ACCEL_CONFIG = 0x1C
    _ACCEL_XOUT_H = 0x3B
    _TEMP_OUT_H = 0x41
    _GYRO_XOUT_H = 0x43

    def __init__(self, bus=1, address=_ADDR):
        """
        Initialize MPU6050 sensor.
        Args:
            bus: I2C bus number (1 for Raspberry Pi)
            address: I2C address of the sensor (default: 0x68)
        """
        self.bus = smbus2.SMBus(bus)
        self.address = address
        self._initialize()

    # -----------------------------
    # Low-level I2C helpers
    # -----------------------------
    def _write_byte(self, reg, value):
        self.bus.write_byte_data(self.address, reg, value)

    def _read_bytes(self, reg, length):
        return self.bus.read_i2c_block_data(self.address, reg, length)

    # -----------------------------
    # Initialization
    # -----------------------------
    def _initialize(self):
        """Wake up and configure the MPU6050."""
        self._write_byte(self._PWR_MGMT_1, 0x00)  # Wake up device
        time.sleep(0.1)
        self._write_byte(self._SMPLRT_DIV, 0x07)  # Sample rate = 1kHz / (1+7) = 125Hz
        self._write_byte(self._CONFIG, 0x00)  # No external sync, 260Hz bandwidth
        self._write_byte(self._GYRO_CONFIG, 0x00)  # ±250°/s
        self._write_byte(self._ACCEL_CONFIG, 0x00)  # ±2g

    # -----------------------------
    # Reading data
    # -----------------------------
    def read(self):
        """
        Read accelerometer, gyroscope, and temperature data.
        Returns:
            (ax, ay, az, gx, gy, gz, temp_c)
        Units:
            accel in g (±2g range)
            gyro in °/s (±250°/s)
            temp in °C
        """
        raw = self._read_bytes(self._ACCEL_XOUT_H, 14)

        # accel
        ax = self._to_signed16(raw[0], raw[1]) / 16384.0
        ay = self._to_signed16(raw[2], raw[3]) / 16384.0
        az = self._to_signed16(raw[4], raw[5]) / 16384.0

        # temp
        temp_raw = self._to_signed16(raw[6], raw[7])
        temp_c = (temp_raw / 340.0) + 36.53

        # gyro
        gx = self._to_signed16(raw[8], raw[9]) / 131.0
        gy = self._to_signed16(raw[10], raw[11]) / 131.0
        gz = self._to_signed16(raw[12], raw[13]) / 131.0

        return ax, ay, az, gx, gy, gz, temp_c

    # -----------------------------
    # Utility
    # -----------------------------
    @staticmethod
    def _to_signed16(high, low):
        v = (high << 8) | low
        return v - 65536 if v & 0x8000 else v
