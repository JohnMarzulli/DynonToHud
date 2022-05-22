import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from dynon_decoder import EfisAndEmsDecoder

RESTFUL_HOST_PORT = 8180


class ServerDecoderInterface(object):
    __DECODER__ = None

    @staticmethod
    def set_decoder(
        decoder: EfisAndEmsDecoder
    ):
        ServerDecoderInterface.__DECODER__ = decoder

    @staticmethod
    def get_situation():
        response = {'Service': 'OFFLINE'}
        if ServerDecoderInterface.__DECODER__ is not None:
            response = ServerDecoderInterface.__DECODER__.get_ahrs_package()

        return json.dumps(
            response,
            indent=4,
            sort_keys=False)


class RestfulHost(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write(ServerDecoderInterface.get_situation().encode())


class HudServer(object):
    """
    Class to handle running a REST endpoint to handle configuration.
    """

    def get_server_ip(
        self
    ):
        """
        Returns the IP address of this REST server.

        Returns:
            string -- The IP address of this server.
        """

        return ''

    def run(
        self
    ):
        """
        Starts the server.
        """

        print(f"localhost = {self.__local_ip__}:{self.__port__}")

        self.__httpd__.serve_forever()

    def stop(
        self
    ):
        if self.__httpd__ is not None:
            self.__httpd__.shutdown()
            self.__httpd__.server_close()

    def __init__(
        self
    ):
        self.__port__ = RESTFUL_HOST_PORT
        self.__local_ip__ = self.get_server_ip()
        server_address = (self.__local_ip__, self.__port__)
        self.__httpd__ = HTTPServer(server_address, RestfulHost)
