"""
This module provides logging functionality for the Spotmicro application.
"""

import logging
from pathlib import Path

from spotmicroai.singleton import Singleton

SPOTMICRO = 'Spotmicro'


class Logger(metaclass=Singleton):
    """A singleton logger class for setting up logging handlers."""

    def __init__(self):
        """Initialize the logger with file and stream handlers."""
        logs_folder = 'logs/'
        Path(logs_folder).mkdir(parents=True, exist_ok=True)

        # create file handler which logs even debug messages
        self.logging_file_handler = logging.FileHandler(logs_folder + SPOTMICRO + '.log')
        # self.logging_file_handler.setLevel(logging.INFO)

        # create console handler with a higher log level
        self.logging_stream_handler = logging.StreamHandler()
        # self.logging_stream_handler.setLevel(logging.DEBUG)

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logging_file_handler.setFormatter(formatter)
        self.logging_stream_handler.setFormatter(formatter)

    def setup_logger(self, logger_name=None):
        """Set up a logger with the given name and return it."""
        if not logger_name:
            logger_name = SPOTMICRO
        else:
            logger_name = SPOTMICRO + ' ' + logger_name

        logger = logging.getLogger(f"{logger_name:<32}")

        logger.setLevel(logging.INFO)

        # add the handlers to logger
        logger.addHandler(self.logging_file_handler)
        logger.addHandler(self.logging_stream_handler)

        return logger
