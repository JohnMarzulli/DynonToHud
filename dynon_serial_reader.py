from datetime import datetime, timedelta, timezone
from time import timezone

import serial

import logger


class DynonSerialReader(object):
    """
    Helper to read data from a Dynon serial connection.
    """

    def __init__(
        self,
        serial_port: str
    ):
        """
        Creates a new reader for the given serial port.

        Arguments:
            serial_port {str} -- The port to read from.
        """
        super().__init__()

        self.serial_port = serial_port
        self.serial_reader = None
        self.__last_read__ = None

        self.open_serial_connection()

    def get_time_since_last_read(
        self
    ) -> timedelta:
        """
        How long has it been since the last successful read?

        Returns:
            timedelta: How long it has been since the last successful read.
        """
        if (self.__last_read__ is None):
            return timedelta(minutes=90)

        return datetime.now(timezone.utc) - self.__last_read__

    def is_time_to_reconnect(
        self
    ) -> bool:
        """
        Has it been long enough since the last read to try a full reconnect?

        Returns:
            bool: Should a full reconnect be attempted?
        """
        time_since_last_read = self.get_time_since_last_read()

        return time_since_last_read.total_seconds > 30

    def start_reconnect(
        self
    ):
        """
        Starts the reconnect process.
        """
        self.__last_read__ = None
        self.serial_reader = None

    def open_serial_connection(
        self
    ):
        """
        Attempts to open the serial connection.
        """

        try:
            if self.serial_reader is None:
                logger.log(
                    'ATTEMPTING to open connection to {0}'.format(
                        self.serial_port))

                self.serial_reader = serial.Serial(
                    self.serial_port,
                    baudrate=115200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=10)

                self.serial_reader.flushInput()

                logger.log(
                    'OPENED serial connection to {0}'.format(
                        self.serial_port))
        except Exception:
            self.serial_reader = None
            logger.log(
                'FAILED attempt to open serial connection to {0}'.format(self.serial_port))

    def read(
        self
    ) -> str:
        """
        Attempts to read from the serial port.

        Returns:
            str -- Any data read from the serial connection. Returns an empty string if unable to read.
        """
        try:
            if self.serial_reader is not None:
                serial_bytes = self.serial_reader.readline()

                if serial_bytes != None and len(serial_bytes) > 0:
                    raw_read = str(serial_bytes, encoding='ascii')
                    logger.log(raw_read)

                    self.__last_read__ = datetime.now(timezone.utc)

                    return raw_read
            else:
                self.open_serial_connection()

            return ""
        except Exception:
            try:
                self.serial_reader.close()
            finally:
                self.serial_reader = None
