# lfd.py
import socket
import time
import sys
import utils
from utils import print_with_timestamp as print

class LFD:
    def __init__(self, server_host='127.0.0.1', server_port=50000, heartbeat_freq=5):
        self.server_host = server_host
        self.server_port = server_port
        self.heartbeat_freq = heartbeat_freq
        self.lfd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        try:
            self.lfd_socket.connect((self.server_host, self.server_port))
            print(f"LFD connected to server at {self.server_host}:{self.server_port}")
            print(f"Heartbeat frequency: {self.heartbeat_freq} seconds")
            
            # Send identification
            self.lfd_socket.send("IDENTIFY:LFD".encode('utf-8'))
            
            # Wait for acknowledgment
            ack = self.lfd_socket.recv(1024).decode('utf-8')
            if ack == "LFD_ACCEPTED":
                print("Server acknowledged LFD connection")
                self.send_heartbeats()
            elif ack == "LFD_REFUSED":
                print("Server refused LFD connection: Another LFD might already be connected")
                self.lfd_socket.close()
            else:
                print(f"Unexpected response from server during identification: {ack}")
                self.lfd_socket.close()
        except ConnectionRefusedError:
            print("Connection to server failed. Make sure the server is running.")

    def send_heartbeats(self):
        while True:
            try:
                print("Sending heartbeat to server S1")
                self.lfd_socket.send("HEARTBEAT".encode('utf-8'))
                response = self.lfd_socket.recv(1024).decode('utf-8')
                if response == "ALIVE":
                    print("Received ALIVE message from server S1")
                else:
                    print(f"Unexpected response from server: {response}")
            except (ConnectionResetError, BrokenPipeError):
                print("Heartbeat failed. Server S1 appears to be down.")
                break
            time.sleep(self.heartbeat_freq)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            heartbeat_freq = int(sys.argv[1])
            if heartbeat_freq <= 0:
                raise ValueError("Heartbeat frequency must be a positive integer")
        except ValueError as e:
            print(f"Invalid heartbeat frequency: {e}")
            print("Using default heartbeat frequency of 5 seconds")
            heartbeat_freq = 5
    else:
        heartbeat_freq = 5
    
    lfd = LFD(heartbeat_freq =heartbeat_freq)
    lfd.start()