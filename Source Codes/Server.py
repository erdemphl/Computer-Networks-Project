import socket
import threading
import logging
import os
from datetime import datetime

# Server configuration
server_host = "localhost" 
server_port = 8080
# Tuple for binding the server
server_address = (server_host, server_port)
# Encoding format for messages
format = "UTF-8"

# Creating a socket for the server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 # Binding the server socket to the address
server_socket.bind(server_address)

# Gateway configuration for a different service
gateway_port = 7070
gateway_address = (server_host, gateway_port) # .

gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Binding the gateway socket
gateway_socket.bind(gateway_address)

gateway_gethumidity_port = 6060
gateway_gethumidity_address = (server_host, gateway_gethumidity_port)
gateway_gethumidity_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Lists for storing temperature and humidity data
last_data = []
temperature_data = []
humidity_data = []

# Logger setup for debugging and log management
logger = logging.getLogger(__name__)

# Extracts sensor type, address, message, and timestamp from the received message
def fetch_msg_timestamp(msg):
    index = msg.rindex("[")
    sensor_index_end = msg.index("]")
    sensor_type = msg[0]
    sensor_address = msg[1:(sensor_index_end + 1)]
    message = msg[(sensor_index_end + 1):index]
    timestamp = msg[index:]
    return sensor_type, sensor_address, message, timestamp

# Processes the message received from a sensor and logs the information
def employee(msg, conn, addr):
    sensor_type, sensor_address, message, timestamp = fetch_msg_timestamp(msg)
    space = " " * (len(timestamp) + 1)
    if sensor_type == "t":
        sensor_address_add = sensor_address[1: sensor_address.index("]")]
        timestamp_add = timestamp[1: timestamp.index("]")]
        temperature_data.append([sensor_address_add, message, timestamp_add])
    elif sensor_type == "h":
        sensor_address_add = sensor_address[1: sensor_address.index("]")]
        timestamp_add = timestamp[1: timestamp.index("]")]
        humidity_data.append([sensor_address_add, message, timestamp_add])
    sensor_port = sensor_address[sensor_address.index(",") + 2: -1]
    logger.info(f"[RECEIVED]\t[('localhost', {addr[1]})]\t{timestamp}\t[('localhost', {sensor_port})] {message}")
    conn.send("Message Received.".encode(format))
    logger.info(f"[SENT]    \t[('localhost', {addr[1]})]\t{space}\tMessage Received.")

# Handles incoming connections and messages on the gateway socket
def handle_gateway(gateway_socket):
    conn, addr = gateway_socket.accept()
    gateway_gethumidity_socket.connect(gateway_gethumidity_address)
    connected = True
    while connected:
        try:
            msg = conn.recv(2048).decode(format)
        except ConnectionResetError:
            break
        employee_thread = threading.Thread(target=employee, args=(msg, conn, addr))
        employee_thread.start()
    conn.close()

# Parses the response string received from the humidity service
def fetch_gethumidity_response(response_string):
    response = []
    start = 0
    end = response_string.find(")")
    temp_str = response_string
    for i in range(int(response_string[-1])):
        sensor_address = temp_str[start:end + 1]
        temp_str = temp_str[end+2:]
        end = temp_str.find(",")
        message = temp_str[start:end]
        temp_str = temp_str[end+1:]
        end = temp_str.find("|")
        timestamp = temp_str[start: end]
        response.append([sensor_address, message, timestamp])
        try:
            temp_str = temp_str[end+1:]
            end = temp_str.find(")")
        except:
            break
    return response

# Initiates the process to get humidity data if the requested file is 'gethumidity.html'
def gethumidity_process(filename):
    if filename != "gethumidity.html":
        return []
    gateway_gethumidity_socket.send("gethumidity".encode(format))
    response = gateway_gethumidity_socket.recv(4096).decode(format)
    if response == "None":
        return []
    return fetch_gethumidity_response(response)

# Selects the appropriate data (temperature, humidity, etc.) based on the requested file
def select_appropriate_data(filename):
    last_data = gethumidity_process(filename)

    select = {"Home.html": None, "temperature.html": temperature_data, "humidity.html": humidity_data, "gethumidity.html": last_data}
    try:
        return select[filename]
    except KeyError:
        return None

# Adds sensor data to the HTML string for dynamic web page generation
def add_data_to_html_string(html_string, data):
    if data is None:
        return html_string
    html_string = html_string.decode(format)
    start_index = html_string.find("<tbody>") + len("<tbody>")
    end_index = html_string.find("</tbody>")
    first_part = html_string[:start_index]
    counter = 1
    second_part = ""
    for packet in data:
        sensor_address = packet[0]
        message = packet[1]
        timestamp = packet[2]
        second_part += f"""<tr>
                               <td>{counter}</td>
                               <td>{sensor_address}</td>
                               <td>{message}</td>
                               <td>{timestamp}</td>
                           </tr>"""
        counter += 1
    third_part = html_string[end_index:]
    merged_html_string = first_part + second_part + third_part
    merged_html_string.strip()

    return merged_html_string.encode("UTF-8")

# Handles incoming client connections and serves requested web pages
def handle_client(conn, addr):
    page_names = ["Home", "temperature", "humidity", "gethumidity", "Home.html", "temperature.html", "humidity.html", "gethumidity.html", ""]
    format = "UTF-8"
    req = conn.recv(2048).decode(format)
    file_name = ""
    try:
        file_name = str(req.split()[1][1:])
    except:
        pass
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if file_name in page_names:
        logger.info("---------------------------------------------------------------------------------")
        logger.info("[REQUEST]\t" + str(addr) + f"\t[{timestamp}]:\n" + req)
        logger.info("---------------------------------------------------------------------------------")
    extension = ""
    if len(file_name) == 0:
        extension = "Home.html"
    elif file_name.endswith(".png"):
        extension = ""
    elif len(file_name) > 0 and (not file_name.endswith(".png")):
        extension = ".html"
    file_name += extension
    data = select_appropriate_data(file_name)
    format = "UTF-8"
    header = 'HTTP/1.1 200 OK\n'
    header += 'Content-Type: text/html\n\n'
    final_response = header.encode(format)

    try:
        with open(f"Website/{file_name}", "rb") as file:
            response = file.read()
            response = add_data_to_html_string(response, data)
    except:
        conn.close()
        return
    final_response += response
    conn.send(final_response)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if file_name in page_names:
        logger.info(f"[RESPONSE]\t" + str(addr) + f"\t[{timestamp}]")
        logger.info("---------------------------------------------------------------------------------")
    conn.close()

# Starts the server and listens for incoming connections
def start():
    gateway_socket.listen()
    logger.info(f"[LISTENING] Server is listening on {server_host}:{gateway_port} for gateway connection")
    thread = threading.Thread(target=handle_gateway, args=(gateway_socket, ))
    thread.start()

    server_socket.listen()
    logger.info(f"[LISTENING] Server is listening on {server_host}:{server_port} for website request")
    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

# Creating necessary directories for logging
if not os.path.exists("Logs"):
    os.makedirs("Logs")
if not os.path.exists("Logs\\ServerLogs"):
    os.makedirs("Logs\\ServerLogs")
# Logger configuration
file_handler = logging.FileHandler("Logs\\ServerLogs\\Server.log", encoding='utf-8')
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

# Starting the server
logger.info("[STARTING] Server is starting...")
start()
