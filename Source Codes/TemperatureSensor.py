import socket
import random
import time

class TemperatureSensor:

    def __init__(self):
        self.current_temperature = None

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
        message = temperature.encode(format)
        sensor_socket.send(message)
        print("[SENT] " + temperature[:-1] + " C")
        rcv_msg = sensor_socket.recv(2048).decode(format)
        print("[RECEIVED] " + rcv_msg)

    def run(self):
        sensor_socket = self.connect_to_gateway()
        while True:
            self.produce_random_temperature()
            self.send_to_gateway(sensor_socket, self.current_temperature)
            time.sleep(1)




temperature_sensor = TemperatureSensor()
temperature_sensor.run()