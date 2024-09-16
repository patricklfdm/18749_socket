# server.py
import socket
import threading
import globals
import utils
from utils import print_with_timestamp as print

class Server:
    def __init__(self, host='127.0.0.1', port=globals.DEFAULT_PORT_NUM):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.clients = {}  # {client_socket: (client_number, unique_id)}
        self.unique_ids = {}  # {unique_id: client_number}
        self.max_clients = globals.MAX_CLIENT_NUM
        self.state = 0
        self.lfd_socket = None
        self.client_counter = 1  # Counter for assigning new client numbers

    def start(self):
        self.server_socket.listen(self.max_clients + 1)  # +1 for LFD
        print(f"Server S1 listening on {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_new_connection, args=(client_socket, addr)).start()

    def handle_new_connection(self, client_socket, addr):
        try:
            # Wait for the IDENTIFY message
            data = client_socket.recv(1024).decode('utf-8')
            if data.startswith("IDENTIFY:"):
                identifier = data.split(":")[1]
                if identifier == "LFD":
                    if not self.lfd_socket:
                        self.lfd_socket = client_socket
                        print(f"LFD connected from {addr}")
                        client_socket.send("LFD_ACCEPTED".encode('utf-8'))  # Send acknowledgment
                        threading.Thread(target=self.handle_lfd, args=(client_socket,)).start()
                    else:
                        print(f"LFD connection from {addr} refused: LFD already connected")
                        client_socket.send("LFD_REFUSED".encode('utf-8'))
                        client_socket.close()
                else:
                    self.handle_client_identification(client_socket, addr, identifier)
            else:
                print(f"Invalid identification from {addr}")
                client_socket.close()
        except Exception as e:
            print(f"Error handling new connection: {e}")
            client_socket.close()

    def handle_client_identification(self, client_socket, addr, unique_id):
        if len(self.clients) < self.max_clients:
            if unique_id in self.unique_ids:
                client_number = self.unique_ids[unique_id]
                # print(f"Reconnected client C{client_number} (ID: {unique_id}) from {addr}")
                print(f"Reconnected client C{client_number} from {addr}")
            else:
                client_number = self.client_counter
                self.unique_ids[unique_id] = client_number
                self.client_counter += 1
                # print(f"New client C{client_number} (ID: {unique_id}) connected from {addr}")
                print(f"New client C{client_number} connected from {addr}")
            
            self.clients[client_socket] = (client_number, unique_id)
            threading.Thread(target=self.handle_client, args=(client_socket, client_number, unique_id)).start()
        else:
            print(f"Connection from {addr} refused: maximum clients reached")
            client_socket.close()

    def handle_lfd(self, lfd_socket):
        while True:
            try:
                data = lfd_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                if data == "HEARTBEAT":
                    print("Received heartbeat from LFD")
                    lfd_socket.send("ALIVE".encode('utf-8'))
                    print("Sent ALIVE message to LFD")
            except ConnectionResetError:
                break
        print("LFD disconnected")
        self.lfd_socket = None

    def handle_client(self, client_socket, client_number, unique_id):
        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                # print(f"Received from client C{client_number} (ID: {unique_id}): {data}")
                print(f"Received from client C{client_number}: {data}")
                self.state += 1
                reply = f"Server reply to C{client_number}: {data.upper()}. Current state: {self.state}"
                # print(f"Sending to client C{client_number} (ID: {unique_id}): {data.upper()}.")
                print(f"Sending to client C{client_number}: {data.upper()}.")
                client_socket.send(reply.encode('utf-8'))
                print(f"Current server state: {self.state}")
            except ConnectionResetError:
                break

        del self.clients[client_socket]
        # print(f"Client C{client_number} (ID: {unique_id}) disconnected")
        print(f"Client C{client_number} disconnected")
        client_socket.close()

if __name__ == "__main__":
    server = Server()
    server.start()