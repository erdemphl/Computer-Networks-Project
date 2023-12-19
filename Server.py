import socket
import threading



server_host = socket.gethostbyname(socket.gethostname())
server_port = 8080
server_address = (server_host, server_port)
format = "UTF-8"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(server_address)


def fetch_msg_timestamp(msg):
    index = msg.rindex("[")
    message = msg[:index]
    timestamp = msg[index:]
    return message, timestamp


def handle_client(conn, addr):
    connected = True
    while connected:
        msg = conn.recv(2048).decode(format)
        message, timestamp = fetch_msg_timestamp(msg)
        space = " " * (len(timestamp) + 1)
        print(f"[RECEIVED]\t[{addr}]\t{timestamp}\t{message}")
        conn.send("Message Received.".encode(format))
        print(f"[SENT]    \t[{addr}]\t{space}\tMessage Received.")
    conn.close()



def start():
    server_socket.listen()
    print(f"[LISTENING] Server is listening on {server_host}:{server_port}")
    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

print("[STARTING] Server is starting...")
start()
