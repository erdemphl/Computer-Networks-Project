import logging
import socket
import random
import time
import os
from datetime import datetime

logger = logging.getLogger(__name__)

"""
This class represents a temperature sensor. It includes methods to connect to a gateway,
generate random temperature readings, send these readings to the gateway, and run the sensor
continuously.
"""
class TemperatureSensor:

    def __init__(self):
        self.current_temperature = None
        self.produce_random_temperature()

    """
    Establishes a connection to the gateway.
    - Sets the gateway's host and port.
    - Creates a socket for the sensor.
    - Attempts to connect to the gateway.
    - Sets up logging, including a file handler specific to this sensor.
    - If the connection is refused, logs a message and exits.
    - Returns the connected socket.
    """
    def connect_to_gateway(self):
        # Gateway connection settings
        gateway_host = "localhost"
        gateway_port = 5050
        gateway_address = (gateway_host, gateway_port)

        sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Create log directories if they don't exist
        if not os.path.exists("Logs"):
            os.makedirs("Logs")
        if not os.path.exists("Logs\\TemperatureSensorLogs"):
            os.makedirs("Logs\\TemperatureSensorLogs")

        # Attempt to connect to the gateway and setup logging
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

    """
    Generates a random temperature reading.
    - Randomly selects a temperature between 20 and 30 degrees Celsius.
    - Updates the current temperature of the sensor.
    """
    def produce_random_temperature(self):
        self.current_temperature = str(random.randint(20, 30)) + str(u"\u2103")

    """
    Sends the current temperature reading to the gateway.
    - Formats the message with the temperature and a timestamp.
    - Tries to send the message to the gateway.
    - Logs the outcome of the attempt (sent or not sent).
    """
    def send_to_gateway(self, sensor_socket, temperature):
        format = "UTF-8"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = "t" + temperature + f"[{timestamp}]"
        message = message.encode(format)
        try:
            sensor_socket.send(message)
        except ConnectionResetError:
            logger.info(f"[NOT SENT]\t[{timestamp}]\t{temperature}")
            return
        logger.info(f"[SENT]    \t[{timestamp}]\t{temperature}")

    """
    Runs the temperature sensor.
    - Connects to the gateway.
    - Enters a loop where it continually sends temperature readings to the gateway.
    - Generates a new temperature reading every second.
    - If interrupted by a KeyboardInterrupt, closes the socket and exits the loop.
    """
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


# Instantiate and run the temperature sensor
temperature_sensor = TemperatureSensor()
temperature_sensor.run()
