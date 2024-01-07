import logging
import socket
import random
import threading
import time
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class HumiditySensor:

    def __init__(self):
        self.current_humidity = None

    """
    Establishes a connection to the gateway.
    - Sets the gateway's host and port.
    - Creates a UDP socket for the sensor.
    - Returns the socket and the gateway address.
    """
    def connect_to_gateway(self, gateway_port):
        self.gateway_host = "localhost"
        gateway_address = (self.gateway_host, gateway_port)
        sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sensor_socket, gateway_address
    """
    Generates a random humidity reading.
    - Randomly selects a humidity percentage between 40% and 90%.
    - Updates the current humidity of the sensor.
    """
    def produce_random_humidity(self):
        self.current_humidity = str(random.randint(40, 90)) + "%"

    """
    Sends the current humidity reading to the gateway.
    - Only sends if humidity is above 80% as a filter condition.
    - Formats the message with the humidity reading and a timestamp.
    - Sends the message to the gateway using UDP.
    - Logs the outcome of the sending attempt.
    """
    def send_humidity_to_gateway(self, sensor_socket, gateway_address, humidity):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if int(humidity[:-1]) <= 80:
            logger.info(f"[NOT SENT]\t[{timestamp}]\t{humidity}")
            return
        format = "UTF-8"
        message = "h" + humidity + f"[{timestamp}]"
        message = message.encode(format)
        sensor_socket.sendto(message, gateway_address)
        logger.info(f"[SENT]    \t[{timestamp}]\t{humidity}")

    """
    Requests a new port from the gateway for the sensor.
    - Sends an empty message to the default gateway port to request a new port.
    - Sets up logging for the sensor.
    - Receives the new port from the gateway and returns it along with the sensor socket.
    """
    def request_port(self):
        format = "UTF-8"
        port = 4040
        new_port = -1
        sensor_socket, gateway_address = self.connect_to_gateway(port)
        sensor_socket.sendto("".encode(format), gateway_address)
        if not os.path.exists("Logs"):
            os.makedirs("Logs")
        if not os.path.exists("Logs\\HumiditySensorLogs"):
            os.makedirs("Logs\\HumiditySensorLogs")
        file_handler = logging.FileHandler(f"Logs\\HumiditySensorLogs\\('localhost', {sensor_socket.getsockname()[1]}).log", encoding='utf-8', mode="w")
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        logger.addHandler(console_handler)
        try:
            new_port = int(sensor_socket.recvfrom(1024)[0].decode(format))

        except ConnectionResetError:
            logger.info("GATEWAY IS OFF")
            exit(0)
        return new_port, sensor_socket

    """
    Continuously notifies the gateway that the sensor is alive.
    - Sends an 'ALIVE' message to the gateway every 3 seconds.
    - Logs each sending attempt.
    """
    def send_alive_to_gateway(self, sensor_socket, gateway_address):
        format = "UTF-8"
        alive = "ALIVE"
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = "h" + f"{alive}[{timestamp}]"
            message = message.encode(format)
            sensor_socket.sendto(message, gateway_address)
            logger.info(f"[SENT]    \t[{timestamp}]\t{alive}")
            time.sleep(3)

    """
    Listens for 'gethumidity' requests and responds with the current humidity.
    - Continuously listens for incoming 'gethumidity' requests.
    - Upon receiving a request, sends back the current humidity along with a timestamp.
    - Logs each received request and sent response.
    """
    def response_gethumidity(self, gethumidity_socket):
        gethumidity_addr = ('localhost', 3030)
        # Listening and responding to gethumidity requests
        while True:
            msg, addr = gethumidity_socket.recvfrom(1024)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[RECEIVED]\t[{timestamp}]\tGET HUMIDITY REQUEST")
            if msg.decode("UTF-8") == "gethumidity":
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                response = f"{self.current_humidity},{timestamp}"
                gethumidity_socket.sendto(response.encode("UTF-8"), gethumidity_addr)
                logger.info(f"[SENT]    \t[{timestamp}]\tGET HUMIDITY RESPONSE: {response[:response.index(',')]}")

    """
    Runs the humidity sensor.
    - Requests a port and connects to the gateway.
    - Starts a thread to continuously send 'ALIVE' messages.
    - Starts another thread to handle responses to 'gethumidity' requests.
    - Continuously generates and sends humidity readings to the gateway.
    """
    def run(self):
        port, get_humiditiy_socket = self.request_port()
        sensor_socket, gateway_address = self.connect_to_gateway(port)
        thread = threading.Thread(target=self.send_alive_to_gateway, args=(sensor_socket, gateway_address))
        thread.start()
        thread_response_gethumidity = threading.Thread(target=self.response_gethumidity, args=(get_humiditiy_socket, ))
        thread_response_gethumidity.start()
        while True:
            self.produce_random_humidity()
            self.send_humidity_to_gateway(sensor_socket, gateway_address, self.current_humidity)
            time.sleep(1)



# Instantiate and run the humidity sensor
humidity_sensor = HumiditySensor()
humidity_sensor.run()
