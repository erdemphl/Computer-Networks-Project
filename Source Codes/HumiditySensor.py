import socket
import random
import threading
import time
from datetime import datetime

class HumiditySensor:

    def __init__(self):
        self.current_humidity = None

    def connect_to_gateway(self):
        gateway_host = socket.gethostbyname(socket.gethostname())
        gateway_port = 4040
        gateway_address = (gateway_host, gateway_port)

        sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        return sensor_socket, gateway_address

    def produce_random_humidity(self):
        self.current_humidity = str(random.randint(40, 90)) + "%"

    def send_humidity_to_gateway(self, sensor_socket, gateway_address, humidity):
        print(humidity)
        if int(humidity[:-1]) <= 80:
            return
        format = "UTF-8"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = humidity + f"[{timestamp}]"
        message = message.encode(format)
        sensor_socket.sendto(message, gateway_address)
        print(f"[SENT]\t[{timestamp}]\t{humidity}")


    def send_alive_to_gateway(self, sensor_socket, gateway_address):
        format = "UTF-8"
        alive = "ALIVE"
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"{alive}[{timestamp}]"
            message = message.encode(format)
            sensor_socket.sendto(message, gateway_address)
            print(f"[SENT]\t[{timestamp}]\t{alive}")
            time.sleep(3)

    def run(self):
        sensor_socket, gateway_address = self.connect_to_gateway()
        thread = threading.Thread(target=self.send_alive_to_gateway, args=(sensor_socket, gateway_address))
        thread.start()
        while True:
            self.produce_random_humidity()
            self.send_humidity_to_gateway(sensor_socket, gateway_address, self.current_humidity)
            time.sleep(1)




humidity_sensor = HumiditySensor()
humidity_sensor.run()