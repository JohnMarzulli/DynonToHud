#!/usr/bin/python3

import datetime
import json
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import dynon_decoder
import dynon_serial_reader

RESTFUL_HOST_PORT = 8180

SERIAL_PORT_0 = '/dev/ttyUSB0'
SERIAL_PORT_1 = '/dev/ttyUSB1'

decoder = dynon_decoder.EfisAndEmsDecoder()


def open_dynon_serials_connection(
    port: str
):
    """
    Attempts to open a serial connection to the Dynon for
    the given port.
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
    """

    while True:
        try:
            serial_connection = open_dynon_serials_connection(port)

            while serial_connection.serial_reader is not None:
                raw_feed = serial_connection.read()
                decoder.decode_efis(raw_feed)
                decoder.decode_ems(raw_feed)
        finally:
            time.sleep(1)


def create_serial_loop_thread(
    port: str
):
    """
    Create a threading object for looping and reading a
    serial port off the Dynon.
    """
    return threading.Thread(
        target=read_and_decode_loop,
        kwargs={"port": port})


def get_situation():
    return json.dumps(
        decoder.get_ahrs_package(),
        indent=4,
        sort_keys=False)


class RestfulHost(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write(get_situation().encode())


class HudServer(object):
    """
    Class to handle running a REST endpoint to handle configuration.
    """

    def get_server_ip(self):
        """
        Returns the IP address of this REST server.

        Returns:
            string -- The IP address of this server.
        """

        return ''

    def run(self):
        """
        Starts the server.
        """

        print("localhost = {}:{}".format(self.__local_ip__, self.__port__))

        self.__httpd__.serve_forever()

    def stop(self):
        if self.__httpd__ is not None:
            self.__httpd__.shutdown()
            self.__httpd__.server_close()

    def __init__(self):
        self.__port__ = RESTFUL_HOST_PORT
        self.__local_ip__ = self.get_server_ip()
        server_address = (self.__local_ip__, self.__port__)
        self.__httpd__ = HTTPServer(server_address, RestfulHost)


serial_port_0_thread = create_serial_loop_thread(SERIAL_PORT_0)
serial_port_1_thread = create_serial_loop_thread(SERIAL_PORT_1)

serial_port_0_thread.start()
serial_port_1_thread.start()

host = HudServer()
host.run()
