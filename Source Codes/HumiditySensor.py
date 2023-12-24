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

    def connect_to_gateway(self, gateway_port):
        self.gateway_host = "localhost"
        gateway_address = (self.gateway_host, gateway_port)
        sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sensor_socket, gateway_address

    def produce_random_humidity(self):
        self.current_humidity = str(random.randint(40, 90)) + "%"

    def send_humidity_to_gateway(self, sensor_socket, gateway_address, humidity):
        logger.info(humidity)
        if int(humidity[:-1]) <= 80:
            return
        format = "UTF-8"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = "h" + humidity + f"[{timestamp}]"
        message = message.encode(format)
        sensor_socket.sendto(message, gateway_address)
        logger.info(f"[SENT]\t[{timestamp}]\t{humidity}")


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

    def send_alive_to_gateway(self, sensor_socket, gateway_address):
        format = "UTF-8"
        alive = "ALIVE"
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = "h" + f"{alive}[{timestamp}]"
            message = message.encode(format)
            sensor_socket.sendto(message, gateway_address)
            logger.info(f"[SENT]\t[{timestamp}]\t{alive}")
            time.sleep(3)


    def response_gethumidity(self, gethumidity_socket):
        gethumidity_addr = ('localhost', 3030)
        while True:
            msg, addr = gethumidity_socket.recvfrom(1024)
            if msg.decode("UTF-8") == "gethumidity":
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                response = f"{self.current_humidity},{timestamp}"
                gethumidity_socket.sendto(response.encode("UTF-8"), gethumidity_addr)
                logger.info(f"[SENT]\t[{timestamp}]\tGET HUMIDITY RESPONSE: {response[:response.index(',')]}")


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




humidity_sensor = HumiditySensor()
humidity_sensor.run()
