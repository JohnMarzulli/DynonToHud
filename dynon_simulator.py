#!/usr/bin/python3

import datetime
import threading
import time
from enum import Enum

import dynon_decoder
import dynon_serial_reader
import rest_service

decoder = dynon_decoder.EfisAndEmsDecoder()
rest_service.ServerDecoderInterface.set_decoder(decoder)


class Port(Enum):
    EFIS = 0
    EMS = 1


class SimulatedDataStream(object):

    def __init__(
        self
    ):
        self.__index__: int = 0
        self.__data_stream__ = []
        self.__start_time__: datetime.datetime = datetime.datetime.utcnow()
        self.__current_offset__: datetime.timedelta = datetime.timedelta(0)

    def add(
        self,
        timedelta: datetime.timedelta,
        serial_data: str
    ):
        self.__data_stream__.append((timedelta, serial_data))

    def get(
        self
    ) -> str:
        # 1 - Step through until we find the first entry with an offset ahead of the current run time.
        # 2 - Sleep the amount of time left
        # 3 - Save the index
        # 4 - if we move past the end of the data, return None

        max_offset = datetime.datetime.utcnow() - self.__start_time__
        length: int = len(self.__data_stream__)

        while self.__index__ < length:
            offset: datetime.timedelta = self.__data_stream__[
                self.__index__][0]

            time_to_sleep = offset.total_seconds() - max_offset.total_seconds()

            if time_to_sleep > 0.0:
                time.sleep(time_to_sleep)

                return self.__data_stream__[self.__index__][1] + "\r\n"

            self.__index__ += 1

        return None


class DynonSimulator(object):

    def get_data(
        self,
        port: Port
    ) -> str:
        if port == Port.EFIS:
            return self.__efis__.get()

        if port == Port.EMS:
            return self.__ems__.get()

        return None

    def __process_playback_line__(
        self,
        playback_line: str
    ):
        if playback_line is None:
            return

        tokens = playback_line.split(' - ')

        if tokens is None:
            return

        if len(tokens) != 4:
            return

        time_and_ms = tokens[0].split(',')

        try:
            recorded_time = datetime.datetime.strptime(
                time_and_ms[0],
                "%Y-%m-%d %H:%M:%S")
            millseconds = datetime.timedelta(milliseconds=int(time_and_ms[1]))
            recorded_time = recorded_time + millseconds
        except:
            return

        dynon_serial = tokens[3].strip()

        if dynon_serial is None:
            return

        if "ATTEMPTING" in dynon_serial:
            return

        if "FAILED" in dynon_serial:
            return

        if "OPENED" in dynon_serial:
            return

        data_length = len(dynon_serial)
        if data_length != 51 and data_length != 119:
            return

        if self.__start_time__ is None:
            self.__start_time__ = recorded_time

        relative_time = recorded_time - self.__start_time__

        if data_length == 51:
            self.__efis__.add(relative_time, dynon_serial)
        elif data_length == 119:
            self.__ems__.add(relative_time, dynon_serial)

    def __parse_playback_file__(
        self,
        data_file: str
    ):
        with open(data_file) as playback_file:
            line = playback_file.readline()

            while line:
                self.__process_playback_line__(line)
                line = playback_file.readline()

    def __init__(
        self,
        data_file: str
    ):
        self.__start_time__ = None
        self.__ems__: SimulatedDataStream = SimulatedDataStream()
        self.__efis__: SimulatedDataStream = SimulatedDataStream()
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
    """

    while True:
        try:
            serial_data = simulator.get_data(port)

            decoder.decode_efis(serial_data)
            decoder.decode_ems(serial_data)
        except Exception as ex:
            print("EX={}".format(ex))


def create_simulator_loop_thread(
    simulator: DynonSimulator,
    port: Port
) -> threading.Thread:
    """
    Create a threading object for looping and reading a
    serial port off the Dynon.
    """
    return threading.Thread(
        target=read_and_decode_loop,
        kwargs={"simulator": simulator, "port": port})


simulator = DynonSimulator("./TestData/dynon_playback.log")

# For simulating a single input without threading.
# read_and_decode_loop(simulator, Port.EFIS)

efis_simulator_thread = create_simulator_loop_thread(simulator, Port.EFIS)
ems_simulator_thread = create_simulator_loop_thread(simulator, Port.EMS)

efis_simulator_thread.start()
ems_simulator_thread.start()

host = rest_service.HudServer()
host.run()
