import datetime
import socket
import threading
from datetime import datetime

gateway_host = socket.gethostbyname(socket.gethostname())

gateway_tcp_port = 5050
gateway_udp_port = 4040
server_port = 8080

gateway_tcp_address = (gateway_host, gateway_tcp_port)
gateway_udp_address = (gateway_host, gateway_udp_port)
server_address = (gateway_host, server_port)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.connect(server_address)

format = "UTF-8"


def tcp_temperature_connection():
    gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gateway_socket.bind(gateway_tcp_address)
    return gateway_socket


def udp_humidity_connection():
    gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gateway_socket.bind(gateway_udp_address)
    return gateway_socket

def fetch_msg_timestamp(msg):
    index = msg.index("[")
    message = msg[:index]
    timestamp = msg[index:]
    return message, timestamp

def handle_temperature_sensor(connection, address):
    print(f"[NEW CONNECTION] {address} connected.")
    connection.settimeout(3)
    connected = True
    while connected:
        try:
            msg = connection.recv(2048).decode(format)
        except socket.timeout:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sensor_off = "TEMP SENSOR OFF"
            msg = f"{sensor_off}[{timestamp}]"
            message = msg.encode(format)
            server_socket.send(message)
            print(f"[SENT]    \t[{server_address}] \t[{timestamp}]\t{sensor_off}")
            rcv_msg = server_socket.recv(2048).decode(format)
            print(f"[RECEIVED]\t[{server_address}] \t{space}\t{rcv_msg}")
            connected = False
            continue
        except ConnectionResetError:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sensor_off = "TEMP SENSOR OFF"
            msg = f"{sensor_off}[{timestamp}]"
            message = msg.encode(format)
            server_socket.send(message)
            print(f"[SENT]    \t[{server_address}] \t[{timestamp}]\t{sensor_off}")
            rcv_msg = server_socket.recv(2048).decode(format)
            print(f"[RECEIVED]\t[{server_address}] \t{space}\t{rcv_msg}")
            connected = False
            continue

        message, timestamp = fetch_msg_timestamp(msg)
        print(f"[RECEIVED]\t[{address}]\t{timestamp}\t{message}")
        space = " " * (len(timestamp) + 1)
        server_socket.send(msg.encode(format))
        print(f"[SENT]    \t[{server_address}] \t{timestamp}\t{message}")
        rcv_msg = server_socket.recv(2048).decode(format)
        print(f"[RECEIVED]\t[{server_address}] \t{space}\t{rcv_msg}")

    connection.close()



def handle_humidity_sensor(msg, address):
    msg = msg.decode(format)
    message, timestamp = fetch_msg_timestamp(msg)
    print(f"[RECEIVED]\t[{address}]\t{timestamp}\t{message}")
    space = " " * (len(timestamp) + 1)
    server_socket.send(msg.encode(format))
    print(f"[SENT]    \t[{server_address}] \t{timestamp}\t{message}")
    rcv_msg = server_socket.recv(2048).decode(format)
    print(f"[RECEIVED]\t[{server_address}] \t{space}\t{rcv_msg}")

def tcp_start():
    gateway_socket = tcp_temperature_connection()
    gateway_socket.listen()
    while True:
        connection, address = gateway_socket.accept()
        thread = threading.Thread(target=handle_temperature_sensor, args=(connection, address))
        thread.start()


def udp_start():
    gateway_socket = udp_humidity_connection()
    while True:
        msg, addr = gateway_socket.recvfrom(1024)
        thread = threading.Thread(target=handle_humidity_sensor, args=(msg, addr))
        thread.start()


def start():
    thread_tcp_sensor = threading.Thread(target=tcp_start)
    thread_udp_sensor = threading.Thread(target=udp_start)
    thread_tcp_sensor.start()
    print(f"[LISTENING] Gateway is listening on {gateway_host}:{gateway_tcp_port} for TCP")
    thread_udp_sensor.start()
    print(f"[LISTENING] Gateway is listening on {gateway_host}:{gateway_udp_port} for UDP")



print("[STARTING] Gateway is starting...")
start()