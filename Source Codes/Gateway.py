import socket
import threading

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


def handle_temperature_sensor(connection, address):
    print(f"[NEW CONNECTION] {address} connected.")

    connected = True
    while connected:
        msg = connection.recv(8).decode(format)
        print(f"[RECEIVED] [{address}] {msg}")
        connection.send("Message Received.".encode(format))
        print(f"[SENT] [{address}] Message Received.")
        server_socket.send(msg.encode(format))
        print(f"[SENT] [{server_address}] {msg}")

    connection.close()


def handle_humidity_sensor(connection, msg, addr):
    msg = msg.decode(format)
    print(f"[RECEIVED] [{addr}] {msg}")
    connection.sendto("Message Received.".encode(format), addr)
    print(f"[SENT] [{addr}] Message Received.")
    server_socket.send(msg.encode(format))
    print(f"[SENT] [{server_address}] {msg}")


def tcp_start():
    gateway_socket = tcp_temperature_connection()
    gateway_socket.listen()
    while True:
        connection, address = gateway_socket.accept()
        thread = threading.Thread(target=handle_temperature_sensor, args=(connection, address))
        thread.start()
        print(f"[ACTIVE TCP CONNECTIONS] {threading.activeCount() - 3}")


def udp_start():
    gateway_socket = udp_humidity_connection()
    while True:
        msg, addr = gateway_socket.recvfrom(1024)
        thread = threading.Thread(target=handle_humidity_sensor, args=(gateway_socket, msg, addr))
        thread.start()


#def send(data):
#    data = data.encode(format)
#    data_length = len(data)
#    send_length = str(data_length).encode(format)
#    send_length += b' ' * (header - len(send_length))
#    client.send(send_length)
#    client.send(data)
#    print(client.recv(2048).decode(FORMAT))


def start():
    thread_tcp_sensor = threading.Thread(target=tcp_start)
    thread_udp_sensor = threading.Thread(target=udp_start)
    thread_tcp_sensor.start()
    print(f"[LISTENING] Gateway is listening on {gateway_host}:{gateway_tcp_port} for TCP")
    thread_udp_sensor.start()
    print(f"[LISTENING] Gateway is listening on {gateway_host}:{gateway_udp_port} for UDP")



print("[STARTING] Gateway is starting...")
start()