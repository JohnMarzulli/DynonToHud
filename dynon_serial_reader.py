import serial

import logger


class DynonSerialReader(object):
    READ_TIMEOUT_SECONDS = 0.5

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

        self.open_serial_connection()

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
                    timeout=DynonSerialReader.READ_TIMEOUT_SECONDS)

                self.serial_reader.flushInput()

                logger.log(
                    'OPENED serial connection to {0}'.format(
                        self.serial_port))
        except:
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
                    return raw_read
            else:
                self.open_serial_connection()

            return ""
        except:
            try:
                self.serial_reader.close()
            finally:
                self.serial_reader = None
