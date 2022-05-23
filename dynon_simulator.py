#!/usr/bin/python3

import datetime
import threading
import time
from enum import Enum

import dynon_decoder
import rest_service

decoder = dynon_decoder.EfisAndEmsDecoder()
rest_service.ServerDecoderInterface.set_decoder(decoder)

VALID_EFIS_DATA_LENGTH = 51
VALID_EMS_DATA_LENGTH = 119


class Port(Enum):
    """
    Valid sources from a Dynon serial connection to be decoded.
    """
    EFIS = 0
    EMS = 1


class SimulatedDataStream(object):
    """
    Simulates a single source from a Dynon serial stream, playing back the 
    data at a "realtime" rate. Skips ahead based on offset times.

    If the consuming code waits for a 2 seconds, then the data fetch moves
    ahead in the playback two seconds as well.
    """

    def __init__(
        self,
        playback_offset: float = 0
    ):
        """
        Create a new playback serial simulator.

        Keyword Arguments:
            playback_offset {float} -- How far forward in the stream will the simulator start. Example: 20 will skip ahead 20 minutes. (default: {0})
        """

        offset = datetime.timedelta(
            minutes=playback_offset)
        self.__index__ = 0
        self.__data_stream__ = []
        self.__start_time__ = (datetime.datetime.utcnow() - offset)
        self.__current_offset__ = datetime.timedelta(0)

    def add(
        self,
        timedelta: datetime.timedelta,
        serial_data: str
    ):
        """
        Adds a single entry into the playback system.
        If the data is added out of sequence, then the data will not be
        played back.

        Arguments:
            timedelta {datetime.timedelta} -- The relative offset of this playback data compared to the start.
            serial_data {str} -- The data to return back and simulate as the serial output.
        """
        self.__data_stream__.append((timedelta, serial_data))

    def get(
        self
    ) -> str:
        """
        Returns a simulated serial output.
        The output is based on relative time passage, with this code pausing the thread to simulate read time.

        Returns:
            str -- Any simulated serial output for the elapsed time. Returns None if the end of the data is reached.
        """

        # 1 - Step through until we find the first entry with an offset ahead of the current run time.
        # 2 - Sleep the amount of time left
        # 3 - Save the index
        # 4 - if we move past the end of the data, return None

        max_offset = datetime.datetime.now(datetime.timezone.utc) - self.__start_time__
        length = len(self.__data_stream__)

        while self.__index__ < length:
            offset = self.__data_stream__[
                self.__index__][0]

            time_to_sleep = offset.total_seconds() - max_offset.total_seconds()

            if time_to_sleep > 0.0:
                time.sleep(time_to_sleep)

                return self.__data_stream__[self.__index__][1] + "\r\n"

            self.__index__ += 1

        return None


def __is_invalid_serial_data__(
    dynon_serial_data_line: str
) -> bool:
    """
    Returns True if the data is determined to be invalid.
    A value of False does not imply that the data is valid.

    Arguments:
        dynon_serial_data_line {str} -- The potential serial data to check if it is invalid.

    Returns:
        bool -- True if the data is invalid. False does not mean the data is proven to be valid.
    """

    if dynon_serial_data_line is None:
        return True

    if "ATTEMPTING" in dynon_serial_data_line:
        return True

    if "FAILED" in dynon_serial_data_line:
        return True

    if "OPENED" in dynon_serial_data_line:
        return True

    data_length = len(dynon_serial_data_line)
    if data_length not in [VALID_EFIS_DATA_LENGTH, VALID_EMS_DATA_LENGTH]:
        return

    return False


def __get_log_timestamp__(
    potential_time_string: str
) -> datetime.datetime:
    """
    Takes a potential token from a log line and attempts to extract
    a timestamp from it.

    Arguments:
        potential_time_string {str} -- A potential timestamp string.

    Returns:
        datetime.datetime -- The extracted timestamp, None if unable to parse one.
    """

    if potential_time_string is None:
        return None

    time_and_ms = potential_time_string.split(',')

    try:
        recorded_time = datetime.datetime.strptime(
            time_and_ms[0],
            "%Y-%m-%d %H:%M:%S")
        millseconds = datetime.timedelta(milliseconds=int(time_and_ms[1]))
        recorded_time = recorded_time + millseconds

        return recorded_time
    except Exception:
        return None


class DynonSimulator(object):
    """
    Simulator for EFIS & EMS data from Dynon serial connections.
    """

    def get_data(
        self,
        port: Port
    ) -> str:
        """
        Gets a simulated data result from the given type of
        serial connection from a Dynon.

        Arguments:
            port {Port} -- If the data should be returned from the EFIS (AHRS) or EMS streams.

        Returns:
            str -- Any simulated serial data for the given port. Returns None of the stream ran out.
        """
        if port == Port.EFIS:
            return self.__efis__.get()

        if port == Port.EMS:
            return self.__ems__.get()

        return None

    def __add_serial_data__(
        self,
        relative_time: datetime.timedelta,
        serial_data: str
    ):
        """
        Adds serial data to the correct simulator bucket.

        Arguments:
            relative_time {datetime.timedelta} -- The time relative to the start of the simulator stream.
            serial_data {str} -- The data to add to a simulator stream.
        """
        if relative_time is None or serial_data is None:
            return

        data_length = len(serial_data)

        if data_length == VALID_EFIS_DATA_LENGTH:
            self.__efis__.add(relative_time, serial_data)
        elif data_length == VALID_EMS_DATA_LENGTH:
            self.__ems__.add(relative_time, serial_data)

    def __process_playback_line__(
        self,
        playback_line: str
    ):
        """
        Takes the potential serial data and adds it to the appropriate playback pool.
        Discards the data if it is not simulated serial data.

        Arguments:
            playback_line {str} -- A line from the log file that is potentially playback data.
        """

        if playback_line is None:
            return

        # Logging separates sections with the spaces.
        # Attempts to tokenize without the spaces in
        # the delimiter will result in the timestamp
        # being split.
        tokens = playback_line.split(' - ')

        if tokens is None:
            return

        if len(tokens) != 4:
            return

        recorded_time = __get_log_timestamp__(tokens[0])

        if recorded_time is None:
            return

        dynon_serial = tokens[3].strip()

        if __is_invalid_serial_data__(dynon_serial):
            return

        if self.__start_time__ is None:
            self.__start_time__ = recorded_time

        relative_time = recorded_time - self.__start_time__

        self.__add_serial_data__(
            relative_time,
            dynon_serial
        )

    def __parse_playback_file__(
        self,
        data_file: str
    ):
        """
        Attempts to extract serial playback data from the given file.

        Arguments:
            data_file {str} -- The path to the data file. Can be relative.
        """

        with open(data_file) as playback_file:
            line = playback_file.readline()

            while line:
                self.__process_playback_line__(line)
                line = playback_file.readline()

    def __init__(
        self,
        data_file: str,
        playback_offset: float = 0
    ):
        """
        Creates a new simulator from the given log file.
        Starts the playback stream at the given time offset (minutes)

        Arguments:
            data_file {str} -- The path the log file to extract playback data from.

        Keyword Arguments:
            playback_offset {float} -- How far into the playback file to start. In terms of minutes. (default: {0})
        """
        self.__start_time__ = None
        self.__ems__ = SimulatedDataStream(playback_offset)
        self.__efis__ = SimulatedDataStream(playback_offset)
        self.__parse_playback_file__(data_file)


def read_and_decode_loop(
    simulator: DynonSimulator,
    port: Port
):
    """
    Starts a USB/Serial reading loop for the given port.
    Attempts to decode the raw feed as both EFIS and EMS
    since both types are regular in length and
    can be determined.

    Arguments:
        simulator {DynonSimulator} -- The simulator that will be used to feed playback streams.
        port {Port} -- The type of Dynon serial stream to be a producer for.
    """

    while True:
        try:
            serial_data = simulator.get_data(port)

            decoder.decode_efis(serial_data)
            decoder.decode_ems(serial_data)

            decoder.garbage_collect()
        except Exception as ex:
            print(f"EX={ex}")


def create_simulator_loop_thread(
    simulator: DynonSimulator,
    port: Port
) -> threading.Thread:
    """
    Create a threading object for looping and reading a
    serial port off the Dynon.

    Arguments:
        simulator {DynonSimulator} -- The simulator that will be used to produce the playback stream.
        port {Port} -- The type of serial data to simulate on this thread.

    Returns:
        threading.Thread -- The thread that will simulate the Dynon serial data.
    """

    return threading.Thread(
        target=read_and_decode_loop,
        kwargs={"simulator": simulator, "port": port})


if __name__ == '__main__':
    simulator = DynonSimulator("./TestData/dynon_playback.log", 20)

    # For simulating a single input without threading.
    # read_and_decode_loop(simulator, Port.EFIS)

    efis_simulator_thread = create_simulator_loop_thread(simulator, Port.EFIS)
    ems_simulator_thread = create_simulator_loop_thread(simulator, Port.EMS)

    efis_simulator_thread.start()
    ems_simulator_thread.start()

    host = rest_service.HudServer()
    host.run()
