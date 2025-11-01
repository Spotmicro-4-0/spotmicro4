"""I2C device helper wrapping smbus interactions."""

from time import sleep

import smbus  # type: ignore

from spotmicroai.singleton import Singleton

# Delay between I2C transactions (in seconds)
I2C_TRANSACTION_DELAY = 0.0001  # 100 microseconds


class I2cDevice(metaclass=Singleton):
    """Provides basic read/write helpers for an I2C device address."""

    def __init__(self, addr: int, port: int = 1):
        """
        Initialize an I2C device helper.

        Args:
            addr: I2C device address (typically 0x00–0x7F).
            port: I2C bus number (default 1 on Raspberry Pi).
        """
        self.addr = addr
        self.bus = smbus.SMBus(port)

    def write_cmd(self, cmd: int) -> None:
        """Write a single command byte."""
        self.bus.write_byte(self.addr, cmd)
        sleep(I2C_TRANSACTION_DELAY)

    def write_cmd_arg(self, cmd: int, data: int) -> None:
        """Write a command and one argument byte."""
        self.bus.write_byte_data(self.addr, cmd, data)
        sleep(I2C_TRANSACTION_DELAY)

    def write_block_data(self, cmd: int, data: list[int]) -> None:
        """Write a block of data to the given command."""
        self.bus.write_block_data(self.addr, cmd, data)
        sleep(I2C_TRANSACTION_DELAY)

    def read(self) -> int:
        """Read a single byte."""
        return self.bus.read_byte(self.addr)

    def read_data(self, cmd: int) -> int:
        """Read one byte from a given command register."""
        return self.bus.read_byte_data(self.addr, cmd)

    def read_block_data(self, cmd: int) -> list[int]:
        """Read a block of bytes from the given command register."""
        return self.bus.read_block_data(self.addr, cmd)
