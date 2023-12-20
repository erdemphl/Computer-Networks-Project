import random
import socket
import threading
import time
from datetime import datetime

gateway_host = socket.gethostbyname(socket.gethostname())

gateway_tcp_port = 5050
gateway_udp_port = 4040
server_port = 7070

gateway_tcp_address = (gateway_host, gateway_tcp_port)
gateway_udp_address = (gateway_host, gateway_udp_port)
server_address = (gateway_host, server_port)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.connect(server_address)

format = "UTF-8"

taken_udp_ports = [gateway_tcp_port]


def tcp_temperature_connection():
    gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gateway_socket.bind(gateway_tcp_address)
    return gateway_socket


def udp_humidity_connection(gateway_udp_address):
    gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gateway_socket.bind(gateway_udp_address)
    return gateway_socket

def fetch_msg_timestamp(msg):
    index = msg.index("[")
    sensor_type = msg[0]
    message = msg[1:index]
    timestamp = msg[index:]
    return sensor_type, message, timestamp


def handle_temperature_sensor(connection, address):
    print(f"[NEW TEMPERATURE SENSOR CONNECTION] {address} connected.")
    connection.settimeout(3)
    sensor_off = "TEMP SENSOR OFF"
    sensor_closed = "TEMP SENSOR CLOSED BY USER"
    connected = True
    try:
        while connected:
            msg = connection.recv(2048).decode(format)
            if len(msg) == 0:
                raise ConnectionResetError
            sensor_type, message, timestamp = fetch_msg_timestamp(msg)
            msg = f"{msg[0]}[{address}]{msg[1:]}"
            print(f"[RECEIVED]\t[{address}]\t{timestamp}\t{message}")
            space = " " * (len(timestamp) + 1)
            server_socket.send(msg.encode(format))
            print(f"[SENT]    \t[{server_address}] \t{timestamp}\t{message}")
            rcv_msg = server_socket.recv(2048).decode(format)
            print(f"[RECEIVED]\t[{server_address}] \t{space}\t{rcv_msg}")

    except socket.timeout:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        space = " " * (len(timestamp) + 1)
        msg = "t" + f"[{address}]" + f"{sensor_off}[{timestamp}]"
        message = msg.encode(format)
        server_socket.send(message)
        print(f"[SENT]    \t[{server_address}] \t[{timestamp}]\t{sensor_off}")
        rcv_msg = server_socket.recv(2048).decode(format)
        print(f"[RECEIVED]\t[{server_address}] \t{space}\t{rcv_msg}")  # sensor off message will be sent to the server after three seconds.

    except ConnectionResetError:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        space = " " * (len(timestamp) + 1)
        msg = "t" + f"[{address}]" + f"{sensor_closed}[{timestamp}]"
        message = msg.encode(format)
        server_socket.send(message)
        print(f"[SENT]    \t[{server_address}] \t[{timestamp}]\t{sensor_closed}")  # if the connection is closed by user, it is directly send to the server.
        rcv_msg = server_socket.recv(2048).decode(format)
        print(f"[RECEIVED]\t[{server_address}] \t{space}\t{rcv_msg}")


def handle_humidity_sensor(msg, address):
    msg = msg.decode(format)
    sensor_type, message, timestamp = fetch_msg_timestamp(msg)
    msg = f"{msg[0]}[{address}]{msg[1:]}"
    print(f"[RECEIVED]\t[{address}]\t{timestamp}\t{message}")
    space = " " * (len(timestamp) + 1)
    server_socket.send(msg.encode(format))
    print(f"[SENT]    \t[{server_address}] \t{timestamp}\t{message}")
    rcv_msg = server_socket.recv(2048).decode(format)
    print(f"[RECEIVED]\t[{server_address}] \t{space}\t{rcv_msg}")

def genereate_unique_udp_port():
    while True:
        port = random.randint(1000, 9999)
        if port in taken_udp_ports:
            continue
        taken_udp_ports.append(port)
        return port


def listen_new_udp_port(addr):
    format = "UTF-8"
    new_port = genereate_unique_udp_port()
    new_gateway_udp_address = (gateway_host, new_port)
    new_gateway_socket = udp_humidity_connection(new_gateway_udp_address)
    new_gateway_socket.sendto(str(new_port).encode(format), addr)
    new_gateway_socket.settimeout(7)
    print(f"[NEW HUMIDITY SENSOR DETECTED] {addr} detected.")
    try:
        while True:
            msg, addr = new_gateway_socket.recvfrom(1024)
            thread = threading.Thread(target=handle_humidity_sensor, args=(msg, addr))
            thread.start()
    except socket.timeout:
        send_off_to_server(addr)
        taken_udp_ports.remove(new_port)



def send_off_to_server(addr):
    msg = "HUMIDITY SENSOR OFF"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_msg = "h" + f"[{addr}]" + f"{msg}[{timestamp}]"
    space = " " * (len(timestamp) + 1)
    server_socket.send(send_msg.encode(format))
    print(f"[SENT]    \t[{server_address}] \t[{timestamp}]\t{msg}")
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
    gateway_socket = udp_humidity_connection(gateway_udp_address)
    while True:
        addr = gateway_socket.recvfrom(1024)[1] # bütün datalar önce buraya sonra başka porta yönlendir
        thread = threading.Thread(target=listen_new_udp_port, args=(addr, ))
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
