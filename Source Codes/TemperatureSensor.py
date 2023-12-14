import socket
import random
import time
from datetime import datetime


class TemperatureSensor:

    def __init__(self):
        self.current_temperature = None
        self.produce_random_temperature()

    def connect_to_gateway(self):
        gateway_host = socket.gethostbyname(socket.gethostname())
        gateway_port = 5050
        gateway_address = (gateway_host, gateway_port)

        sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sensor_socket.connect(gateway_address)

        return sensor_socket

    def produce_random_temperature(self):
        self.current_temperature = str(random.randint(20, 30)) + str(u"\u2103")

    def send_to_gateway(self, sensor_socket, temperature):
        format = "UTF-8"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = temperature + f"[{timestamp}]"
        message = message.encode(format)
        sensor_socket.send(message)
        print(f"[SENT]\t[{timestamp}]\t{temperature}")


    def run(self):
        sensor_socket = self.connect_to_gateway()
        while True:
            self.send_to_gateway(sensor_socket, self.current_temperature)
            self.produce_random_temperature()
            time.sleep(1)




temperature_sensor = TemperatureSensor()
temperature_sensor.run()