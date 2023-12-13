import socket
import threading


server_host = socket.gethostbyname(socket.gethostname())
server_port = 8080
server_address = (server_host, server_port)
format = "UTF-8"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(server_address)


def handle_client(conn, addr):
    connected = True
    while connected:
        msg = conn.recv(8).decode(format)
        print(f"[RECEIVED] [{addr}] {msg}")
        conn.send("Message Received.".encode(format))
        print(f"[SENT] [{addr}] Message Received.")
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
