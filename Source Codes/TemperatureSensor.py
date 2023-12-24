import logging
import socket
import random
import time
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class TemperatureSensor:

    def __init__(self):
        self.current_temperature = None
        self.produce_random_temperature()

    def connect_to_gateway(self):
        gateway_host = "localhost"
        gateway_port = 5050
        gateway_address = (gateway_host, gateway_port)

        sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not os.path.exists("Logs"):
            os.makedirs("Logs")
        if not os.path.exists("Logs\\TemperatureSensorLogs"):
            os.makedirs("Logs\\TemperatureSensorLogs")

        try:
            sensor_socket.connect(gateway_address)
            file_handler = logging.FileHandler(f'Logs\\TemperatureSensorLogs\\({gateway_host}, {sensor_socket.getsockname()[1]}).log', encoding='utf-8', mode="w")
            logger.addHandler(file_handler)
            logger.setLevel(logging.INFO)
            console_handler = logging.StreamHandler()
            logger.addHandler(console_handler)
        except ConnectionRefusedError:
            file_handler = logging.FileHandler(f"Logs\\TemperatureSensorLogs\\('{gateway_host}', '{sensor_socket.getsockname()[1]}')", encoding='utf-8', mode="w")
            logger.addHandler(file_handler)
            logger.setLevel(logging.INFO)
            console_handler = logging.StreamHandler()
            logger.addHandler(console_handler)
            logger.info("GATEWAY IS OFF")
            exit(0)
        return sensor_socket

    def produce_random_temperature(self):
        self.current_temperature = str(random.randint(20, 30)) + str(u"\u2103")

    def send_to_gateway(self, sensor_socket, temperature):
        format = "UTF-8"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = "t" + temperature + f"[{timestamp}]"
        message = message.encode(format)
        try:
            sensor_socket.send(message)
        except ConnectionResetError:
            logger.info(f"{temperature}")
            return
        logger.info(f"[SENT]\t[{timestamp}]\t{temperature}")

    def run(self):
        sensor_socket = self.connect_to_gateway()
        while True:
            self.send_to_gateway(sensor_socket, self.current_temperature)
            self.produce_random_temperature()
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                sensor_socket.close()
                break




temperature_sensor = TemperatureSensor()
temperature_sensor.run()
