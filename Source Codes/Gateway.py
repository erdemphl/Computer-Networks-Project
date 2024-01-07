import logging
import random
import socket
import threading
import time
from datetime import datetime
import os

gateway_host = "localhost"

gateway_udp_port = 4040
gateway_gethumidity_port = 6060
gateway_tcp_port = 5050
server_port = 7070

gateway_tcp_address = (gateway_host, gateway_tcp_port)
gateway_udp_address = (gateway_host, gateway_udp_port)
server_address = (gateway_host, server_port)
gateway_gethumidity_address = (gateway_host, gateway_gethumidity_port)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

gateway_gethumidity_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
gateway_gethumidity_socket.bind(gateway_gethumidity_address)

format = "UTF-8"

logger = logging.getLogger(__name__)


def try_to_connect_server(server_socket): # if the server is closed, this waits for it so that it starts.
    while True:
        try:
            server_socket.connect(server_address)
            break
        except ConnectionRefusedError:
            pass

def server_connection():
    try:
        server_socket.connect(server_address)
    except ConnectionRefusedError: # if server is close, wait for it.
        listen_server_thread = threading.Thread(target=try_to_connect_server, args=(server_socket, ))
        listen_server_thread.start()


def tcp_temperature_connection(): # tcp connection for temperature sensor
    gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gateway_socket.bind(gateway_tcp_address)
    return gateway_socket


def udp_humidity_connection(gateway_udp_address): # udp binding for humidity sensor
    gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gateway_socket.bind(gateway_udp_address)
    return gateway_socket

def fetch_msg_timestamp(msg): # fetch the recieved data from the sensors, timestapmp data etc.
    # msg format = "sensor_type, data, timestamp", h or t for type
    index = msg.index("[")
    sensor_type = msg[0]
    message = msg[1:index]
    timestamp = msg[index:]
    return sensor_type, message, timestamp


def handle_temperature_sensor(connection, address): # handle the temperature sensor
    logger.info(f"[NEW TEMPERATURE SENSOR CONNECTION] [('localhost', {address[1]})] connected.")
    connection.settimeout(3) # if the dont come a data from the sensor for 3 seconds, temp sensor off message will be sent server.
    sensor_off = "TEMP SENSOR OFF"
    connected = True
    try:
        while connected:
            msg = connection.recv(2048).decode(format)
            if len(msg) == 0:
                raise ConnectionResetError
            sensor_type, message, timestamp = fetch_msg_timestamp(msg)
            msg = f"{msg[0]}[{address}]{msg[1:]}"
            logger.info(f"[RECEIVED]\t[('localhost', {address[1]})]\t{timestamp}\t{message}")
            space = " " * (len(timestamp) + 1)
            try:
                server_socket.send(msg.encode(format))
            except OSError:
                logger.info(f"[SENT]    \t[('localhost', {server_address[1]})] \t{timestamp}\t{message}")
                continue
            logger.info(f"[SENT]    \t[('localhost', {server_address[1]})] \t{timestamp}\t{message}")
            rcv_msg = server_socket.recv(2048).decode(format)
            logger.info(f"[RECEIVED]\t[('localhost', {server_address[1]})] \t{space}\t{rcv_msg}")

    except socket.timeout:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        space = " " * (len(timestamp) + 1)
        msg = "t" + f"[{address}]" + f"{sensor_off}[{timestamp}]"
        message = msg.encode(format)
        try:
            server_socket.send(message)
        except OSError:
            logger.info(f"[SENT]    \t[('localhost', {server_address[1]})] \t[{timestamp}]\t[('localhost', {address[1]})] {sensor_off}")
            connection.close()
            return
        logger.info(f"[SENT]    \t[('localhost', {server_address[1]})] \t[{timestamp}]\t[('localhost', {address[1]})] {sensor_off}")
        rcv_msg = server_socket.recv(2048).decode(format)
        logger.info(f"[RECEIVED]\t[('localhost', {server_address[1]})] \t{space}\t{rcv_msg}")  # sensor off message will be sent to the server after three seconds.
        connection.close()

    except ConnectionResetError:
        time.sleep(3)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        space = " " * (len(timestamp) + 1)
        msg = "t" + f"[{address}]" + f"{sensor_off}[{timestamp}]"
        message = msg.encode(format)
        try:
            server_socket.send(message)
        except OSError:
            logger.info(f"[SENT]    \t[('localhost', {server_address[1]})] \t[{timestamp}]\t[('localhost', {address[1]})] {sensor_off}")  # if the connection is closed by user, it is directly send to the server.
            connection.close()
            return
        logger.info(f"[SENT]    \t[('localhost', {server_address[1]})] \t[{timestamp}]\t[('localhost', {address[1]})] {sensor_off}")  # if the connection is closed by user, it is directly send to the server.
        rcv_msg = server_socket.recv(2048).decode(format)
        logger.info(f"[RECEIVED]\t[('localhost', {server_address[1]})] \t{space}\t{rcv_msg}")
        connection.close()


"""
Handle incoming messages from a humidity sensor.
- Decodes the message from the sensor.
- Extracts sensor type, message, and timestamp from the message.
- Reconstructs the message with the sensor's address.
- Logs the received message.
- Attempts to forward the message to the server.
- Logs the outcome of the attempt (sent or failed).
"""
def handle_humidity_sensor(msg, address):
    msg = msg.decode(format)
    sensor_type, message, timestamp = fetch_msg_timestamp(msg)
    msg = f"{msg[0]}[{address}]{msg[1:]}"
    logger.info(f"[RECEIVED]\t[('localhost', {address[1]})]\t{timestamp}\t{message}")
    space = " " * (len(timestamp) + 1)
    try:
        server_socket.send(msg.encode(format))
    except OSError:
        logger.info(f"[SENT]    \t[('localhost', {server_address[1]})] \t{timestamp}\t{message}")
        return
    logger.info(f"[SENT]    \t[('localhost', {server_address[1]})] \t{timestamp}\t{message}")
    try:
        rcv_msg = server_socket.recv(2048).decode(format)
    except ConnectionResetError:
        return
    logger.info(f"[RECEIVED]\t[('localhost', {server_address[1]})] \t{space}\t{rcv_msg}")


"""
Generate a unique UDP port number.
- Randomly selects a port number between 1000 and 9999.
- Checks if the port is already taken. If yes, selects another port.
- Once a unique port is found, adds it to the list of taken ports and returns it.
"""
def genereate_unique_udp_port():
    while True:
        port = random.randint(1000, 9999)
        if port in taken_udp_ports:
            continue
        taken_udp_ports.append(port)
        return port

"""
Listen on a newly generated UDP port for humidity sensor data.
- Generates a unique UDP port and binds a socket to it.
- Sends the new port number back to the sensor.
- Enters a loop to continuously receive data from the sensor.
- For each new message, starts a new thread to handle the sensor data.
- If a timeout occurs, handles the sensor disconnection and cleans up resources.
"""
def listen_new_udp_port(addr):
    format = "UTF-8"
    new_port = genereate_unique_udp_port()
    new_gateway_udp_address = (gateway_host, new_port)
    new_gateway_socket = udp_humidity_connection(new_gateway_udp_address)
    new_gateway_socket.sendto(str(new_port).encode(format), addr)
    new_gateway_socket.settimeout(7)
    logger.info(f"[NEW HUMIDITY SENSOR DETECTED] [('localhost', {addr[1]})] detected.")
    try:
        while True:
            msg, address = new_gateway_socket.recvfrom(1024)
            thread = threading.Thread(target=handle_humidity_sensor, args=(msg, addr))
            thread.start()
    except socket.timeout:
        send_off_to_server(addr, new_gateway_socket)
        taken_udp_ports.remove(new_port)
        active_humidity.remove(addr)


"""
Notify the server when a humidity sensor is offline.
- Constructs a 'sensor off' message with a timestamp.
- Attempts to send this message to the server.
- Logs the action (sent or failed).
- Closes the socket if sending fails.
"""
def send_off_to_server(addr, new_gateway_socket):
    msg = "HUMIDITY SENSOR OFF"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_msg = "h" + f"[{addr}]" + f"{msg}[{timestamp}]"
    space = " " * (len(timestamp) + 1)
    try:
        server_socket.send(send_msg.encode(format))
    except OSError:
        logger.info(f"[SENT]    \t[('localhost', {server_address[1]})] \t[{timestamp}]\t[('localhost', {addr[1]})] {msg}")
        new_gateway_socket.close()
        return
    logger.info(f"[SENT]    \t[('localhost', {server_address[1]})] \t[{timestamp}]\t[('localhost', {addr[1]})] {msg}")
    rcv_msg = server_socket.recv(2048).decode(format)
    logger.info(f"[RECEIVED]\t[('localhost', {server_address[1]})] \t{space}\t{rcv_msg}")

"""
Start the TCP server for handling temperature sensors.
- Sets up a TCP socket and listens for incoming connections.
- For each new connection, starts a new thread to handle the temperature sensor data.
"""
def tcp_start():
    gateway_socket = tcp_temperature_connection()
    gateway_socket.listen()
    while True:
        connection, address = gateway_socket.accept()
        thread = threading.Thread(target=handle_temperature_sensor, args=(connection, address))
        thread.start()

"""
Start the UDP server for detecting and handling humidity sensors.
- Sets up a UDP socket and listens for new sensor announcements.
- For each detected sensor, adds its address to a list and starts a new thread to handle it.
"""
def udp_start():
    gateway_socket = udp_humidity_connection(gateway_udp_address)
    while True:
        addr = gateway_socket.recvfrom(1024)[1]
        active_humidity.append(addr)
        thread = threading.Thread(target=listen_new_udp_port, args=(addr, ))
        thread.start()


#Parse a humidity sensor's response message.
#Extracts the current humidity reading and the timestamp from the response.
def fetch_gethumidity_msg(response):
    middle = response.index(",")
    current_humidity = response[:middle]
    timestamp = response[middle + 1:]
    return current_humidity, timestamp

"""
Process a 'gethumidity' request from the server.
- Sends a request to all active humidity sensors to get the current humidity data.
- Receives responses from the sensors and compiles them.
- Sends the compiled data back to the server.
"""
def gethumidity_process(msg, gethumidity_socket, server_gethumidity_socket, addr):
    responses = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if msg == "gethumidity":
        for addr in active_humidity:
            gethumidity_socket.sendto(msg.encode(format), addr)
            logger.info(f"[SENT]    \t[('localhost', {addr[1]})] \t[{timestamp}]\tGET HUMIDITY REQUEST")
            try:
                response, address = gethumidity_socket.recvfrom(1024)
                fetched_msg = fetch_gethumidity_msg(response.decode(format))
                responses.append([address, fetched_msg[0], fetched_msg[1]])
                logger.info(f"[RECEIVED]\t[('localhost', {address[1]})] \t[{fetched_msg[1]}]\tGET HUMIDITY RESPONSE: {fetched_msg[0]}")
            except ConnectionResetError:
                if len(active_humidity) == 1:
                    server_gethumidity_socket.send("None".encode(format))
                continue
    response_string = ""
    for response in responses:
        response_string += f"{response[0]},{response[1]},{response[2]}|"
    response_string += f"{len(responses)}"
    server_gethumidity_socket.send(response_string.encode(format))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[SENT]    \t[('localhost', {addr[1]})] \t[{timestamp}]\tALL GET HUMIDITY RESPONSE SENT TO THE SERVER")


# Listens for 'gethumidity' requests from the server and initiates the humidity data retrieval process.
def listen_server_gethumidity():
    gateway_gethumidity_socket.listen()
    connection, address = gateway_gethumidity_socket.accept()
    gethumidity_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gethumidity_socket.bind((gateway_host, 3030))
    while True:
        try:
            msg = connection.recv(1024).decode(format)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[RECEIVED]\t[('localhost', {address[1]})] \t[{timestamp}]\tGET HUMIDITY REQUEST FROM THE SERVER")
        except:
            continue
        if msg == "gethumidity":
            thread = threading.Thread(target=gethumidity_process, args=(msg, gethumidity_socket, connection, address))
            thread.start()

"""
Initialize and start the gateway server.
- Sets up connections for TCP and UDP.
- Starts listening for temperature and humidity sensors.
- Starts a separate thread for handling 'gethumidity' requests from the server.
"""
def start():
    server_connection()
    thread_listen_gethumidity = threading.Thread(target=listen_server_gethumidity)
    thread_listen_gethumidity.start()
    thread_tcp_sensor = threading.Thread(target=tcp_start)
    thread_udp_sensor = threading.Thread(target=udp_start)
    thread_tcp_sensor.start()
    logger.info(f"[LISTENING] Gateway is listening on {gateway_host}:{gateway_tcp_port} for TCP")
    thread_udp_sensor.start()
    logger.info(f"[LISTENING] Gateway is listening on {gateway_host}:{gateway_udp_port} for UDP")


if not os.path.exists("Logs"):
    os.makedirs("Logs")
if not os.path.exists("Logs\\GatewayLogs"):
    os.makedirs("Logs\\GatewayLogs")
file_handler = logging.FileHandler('Logs\\GatewayLogs\\Gateway.log', encoding='utf-8')
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

logger.info("[STARTING] Gateway is starting...")
start()
