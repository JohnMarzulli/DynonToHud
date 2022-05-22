#!/usr/bin/python3

import threading
import time

import dynon_decoder
import dynon_serial_reader
import rest_service

SERIAL_PORT_0 = '/dev/ttyUSB0'
SERIAL_PORT_1 = '/dev/ttyUSB1'

decoder = dynon_decoder.EfisAndEmsDecoder()
rest_service.ServerDecoderInterface.set_decoder(decoder)


def open_dynon_serials_connection(
    port: str
) -> dynon_serial_reader.DynonSerialReader:
    """
    Attempts to open a serial connection to the Dynon for
    the given port.

    Arguments:
        port {str} -- The path to the serial device to read from.

    Returns:
        dynon_serial_reader.DynonSerialReader -- The new reader for the serial port.
    """

    serial_connection = None

    while serial_connection is None or serial_connection.serial_reader is None:
        try:
            serial_connection = dynon_serial_reader.DynonSerialReader(port)
        finally:
            if serial_connection is None or serial_connection.serial_reader is None:
                time.sleep(1)

    return serial_connection


def read_and_decode_loop(
    port: str
):
    """
    Starts a USB/Serial reading loop for the given port.
    Attempts to decode the raw feed as both EFIS and EMS
    since both types are regular in length and
    can be determined.

    Arguments:
        port {str} -- The path to the serial device to read from.
    """

    while True:
        try:
            serial_connection = open_dynon_serials_connection(port)

            while serial_connection.serial_reader is not None:
                raw_feed = serial_connection.read()
                decoder.decode_efis(raw_feed)
                decoder.decode_ems(raw_feed)
                decoder.garbage_collect()

                if serial_connection.is_time_to_reconnect():
                    serial_connection.start_reconnect()
        except Exception:
            serial_connection = None
        finally:
            time.sleep(1)


def create_serial_loop_thread(
    port: str
) -> threading.Thread:
    """
    Create a threading object for looping and reading a
    serial port off the Dynon.

    Arguments:
        port {str} -- The path to the serial device to read from.

    Returns:
        threading.Thread -- The thread responsible for reading the serial port.
    """

    return threading.Thread(
        target=read_and_decode_loop,
        kwargs={"port": port})


serial_port_0_thread = create_serial_loop_thread(SERIAL_PORT_0)
serial_port_1_thread = create_serial_loop_thread(SERIAL_PORT_1)

serial_port_0_thread.start()
serial_port_1_thread.start()

host = rest_service.HudServer()
host.run()
