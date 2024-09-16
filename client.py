# client.py
import socket
import threading
import uuid
import enum
import sys
import utils
from utils import print_with_timestamp as print

class ClientState(enum.Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    WAITING_RESPONSE = 2

class Client:
    def __init__(self, host='127.0.0.1', port=50000, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.unique_id = str(uuid.uuid4())
        self.client_socket = None
        self.state = ClientState.DISCONNECTED
        self.receive_thread = None
        self.lock = threading.Lock()
        self.response_received = threading.Event()
        self.if_first_connect = True

    def connect(self):
        if self.state != ClientState.DISCONNECTED:
            print(f"C{self.client_id} is already connected or in the process of connecting.")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            with self.lock:
                self.state = ClientState.CONNECTED
            print(f"C{self.client_id} connected to server at {self.host}:{self.port}")
            
            self.client_socket.send(f"IDENTIFY:{self.unique_id}".encode('utf-8'))
            
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()
        except ConnectionRefusedError:
            print(f"C{self.client_id}: Connection refused. Make sure the server is running.")

    def disconnect(self):
        if self.state == ClientState.DISCONNECTED:
            print(f"C{self.client_id} is not connected.")
            return

        with self.lock:
            self.state = ClientState.DISCONNECTED
        if self.client_socket:
            self.client_socket.close()
        if self.receive_thread:
            self.receive_thread.join()
        print(f"C{self.client_id} disconnected from server.")

    def receive_messages(self):
        while self.state != ClientState.DISCONNECTED:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    print(f"C{self.client_id} received: {message}")
                    with self.lock:
                        if self.state == ClientState.WAITING_RESPONSE:
                            self.state = ClientState.CONNECTED
                            self.response_received.set()
                else:
                    print(f"C{self.client_id}: Server closed the connection.")
                    self.disconnect()
            except ConnectionResetError:
                print(f"C{self.client_id}: Connection to server lost.")
                self.disconnect()
            except OSError:
                break

    def send_message(self, message):
        if self.state != ClientState.CONNECTED:
            print(f"C{self.client_id}: Not in a state to send messages. Current state: {self.state}")
            return

        try:
            print(f"C{self.client_id} sending: {message}")
            self.client_socket.send(message.encode('utf-8'))
            with self.lock:
                self.state = ClientState.WAITING_RESPONSE
            self.response_received.clear()
            self.response_received.wait(timeout=5)  # Wait for up to 5 seconds for a response
        except ConnectionResetError:
            print(f"C{self.client_id}: Connection to server lost.")
            self.disconnect()

    def run(self):
        while True:
            if self.state == ClientState.DISCONNECTED and not self.if_first_connect:
                command = input(utils.add_timestamp(f"C{self.client_id} Enter 'connect' to connect to server: "))
                if command.lower() == 'connect':
                    self.connect()
                continue
            elif self.state == ClientState.DISCONNECTED and self.if_first_connect:
                self.if_first_connect = False
                self.connect()
                continue

            message = input(utils.add_timestamp(f"C{self.client_id} Enter message (or 'exit'/'quit' to disconnect): "))
            if message.lower() in ['exit', 'quit']:
                self.disconnect()
            else:
                self.send_message(message)

if __name__ == "__main__":
    client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    client = Client(client_id=client_id)
    client.run()